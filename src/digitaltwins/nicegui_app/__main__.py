"""Iniciar solo en loopback; no ejecutar experimentos desde la interfaz."""
import argparse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8087, help="Puerto local (predeterminado: 8087)")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("El puerto debe estar entre 1024 y 65535")
    from .app import launch
    launch(args.port)


if __name__ == "__main__":
    main()
