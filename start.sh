#!/bin/bash
# Gerar host keys se não existirem
ssh-keygen -A

# Iniciar o SSH
/usr/sbin/sshd -D
