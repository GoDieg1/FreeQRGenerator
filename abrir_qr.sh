#!/bin/bash
cd "$(dirname "$0")"
source ~/qr-env/bin/activate
python generador_qr.py
