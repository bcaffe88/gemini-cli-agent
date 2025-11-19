FROM alpine:latest

RUN apk update && apk add openssh bash

RUN adduser -D agent && echo "agent:agent123" | chpasswd

RUN mkdir /home/agent/.ssh && chmod 700 /home/agent/.ssh

COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 22

CMD ["/start.sh"]
