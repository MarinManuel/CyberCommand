#!/usr/bin/env bash
socat pty,raw,echo=0,link=./tty0 pty,raw,echo=0,link=./tty1