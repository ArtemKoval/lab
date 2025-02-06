FROM node:latest

RUN mkdir -p /home/node/payments_app/node_modules && chown -R node:node /home/node/payments_app

WORKDIR /home/node/payments_app

COPY package*.json ./

USER node

RUN npm install

COPY --chown=node:node . .

EXPOSE 9000

CMD ["npm", "run", "prod"]
