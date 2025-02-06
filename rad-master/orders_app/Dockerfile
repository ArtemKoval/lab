FROM node:latest

RUN mkdir -p /home/node/orders_app/node_modules && chown -R node:node /home/node/orders_app

WORKDIR /home/node/orders_app

COPY package*.json ./

USER node

RUN npm install

COPY --chown=node:node . .

EXPOSE 9000

CMD ["npm", "run", "prod"]
