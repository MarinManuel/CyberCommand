# in VirtualBox, create a serial port using Host Pipe, do not check "use existing" and enter name: `/tmp/vboxtty`
socat unix-connect:/tmp/vboxtty pty,raw,echo=0,link=./tty1
