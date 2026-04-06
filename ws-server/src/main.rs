use axum::{
    Router,
    extract::ws::{Message, WebSocket, WebSocketUpgrade},
    response::IntoResponse,
    routing::get,
};
use futures_util::{SinkExt, StreamExt};
use ngrok::prelude::*;
use std::sync::Arc;
use tokio::sync::broadcast;
use tracing::info;

const CHANNEL_CAPACITY: usize = 128;

#[derive(Clone)]
struct AppState {
    tx: Arc<broadcast::Sender<String>>,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter("ws_server=debug,info")
        .init();

    let (tx, _rx) = broadcast::channel::<String>(CHANNEL_CAPACITY);
    let state = AppState { tx: Arc::new(tx) };

    let app = Router::new()
        .route("/ws", get(ws_handler))
        .with_state(state);

    // Build ngrok tunnel — reads NGROK_AUTHTOKEN from env
    let listener = ngrok::Session::builder()
        .authtoken_from_env()
        .connect()
        .await?
        .http_endpoint()
        .listen()
        .await?;

    let url = listener.url().to_string();
    info!("╔══════════════════════════════════════════╗");
    info!("║  WebSocket server live via ngrok          ║");
    info!("║  URL : {:<33}║", format!("{}/ws", url));
    info!("╚══════════════════════════════════════════╝");

    axum::serve(listener, app).await?;
    Ok(())
}

async fn ws_handler(
    ws: WebSocketUpgrade,
    axum::extract::State(state): axum::extract::State<AppState>,
) -> impl IntoResponse {
    ws.on_upgrade(move |socket| handle_socket(socket, state))
}

async fn handle_socket(socket: WebSocket, state: AppState) {
    let (mut sender, mut receiver) = socket.split();
    let mut rx = state.tx.subscribe();

    // Forward broadcast messages → this client
    let mut send_task = tokio::spawn(async move {
        while let Ok(msg) = rx.recv().await {
            if sender.send(Message::Text(msg.into())).await.is_err() {
                break;
            }
        }
    });

    // Receive from client → broadcast to all
    let tx = Arc::clone(&state.tx);
    let mut recv_task = tokio::spawn(async move {
        while let Some(Ok(msg)) = receiver.next().await {
            match msg {
                Message::Text(text) => {
                    info!("recv: {text}");
                    let _ = tx.send(text.to_string());
                }
                Message::Close(_) => break,
                _ => {}
            }
        }
    });

    // Abort the other task when one finishes
    tokio::select! {
        _ = &mut send_task => recv_task.abort(),
        _ = &mut recv_task => send_task.abort(),
    }

    info!("client disconnected");
}
