import argparse
import asyncio
import json
import logging

from service.asr.asr_factory import ASRFactory
from service.vad.vad_factory import VADFactory
from server import Server


def parse_args():
    parser = argparse.ArgumentParser(
        description="VoiceStreamAI Server: Real-time audio transcription "
        "using self-hosted Whisper and WebSocket."
    )
    parser.add_argument(
        "--asr-type",
        type=str,
        default="vosk",
        help="Type of ASR pipeline to use (e.g., 'whisper')",
    )
    parser.add_argument(
        "--asr-args",
        type=str,
        default='{"model_size": "large-v3"}',
        help="JSON string of additional arguments for ASR pipeline",
    )
    parser.add_argument(
        "--vad-type",
        type=str,
        default="vosk",
        help="Type of ASR pipeline to use (e.g., 'whisper')",
    )
    parser.add_argument(
        "--vad-args",
        type=str,
        default='{"model_size": "large-v3"}',
        help="JSON string of additional arguments for ASR pipeline",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host for the WebSocket server",
    )
    parser.add_argument(
        "--port", type=int, default=8765, help="Port for the WebSocket server"
    )
    parser.add_argument(
        "--certfile",
        type=str,
        default=None,
        help="The path to the SSL certificate (cert file) if using secure "
        "websockets",
    )
    parser.add_argument(
        "--keyfile",
        type=str,
        default=None,
        help="The path to the SSL key file if using secure websockets",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="error",
        choices=["debug", "info", "warning", "error"],
        help="Logging level: debug, info, warning, error. default: error",
    )
    return parser.parse_args()


async def run_server(args):
    logging.basicConfig()
    logging.getLogger().setLevel(args.log_level.upper())

    try:
        asr_args = json.loads(args.asr_args)
        vad_args = json.loads(args.vad_args)
    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON аргументов: {e}")
        return

    asr_pipeline = ASRFactory.create_asr_pipeline(args.asr_type, **asr_args)
    vad_pipeline = VADFactory.create_vad_pipeline(args.vad_type, **asr_args)

    server = Server(
        vad_pipeline,
        asr_pipeline,
        host=args.host,
        port=args.port,
        sampling_rate=16000,
        samples_width=2,
        certfile=args.certfile,
        keyfile=args.keyfile,
    )

    await server.start()
    await asyncio.Future()  # Блокирует выполнение, чтобы сервер оставался активным


def main():
    args = parse_args()
    asyncio.run(run_server(args))


if __name__ == "__main__":
    main()
