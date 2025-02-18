FROM node:16-alpine as builder
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
RUN npm run build


FROM nginx 

#The to copy directory has been mentioned in nginx image, copied the path from recommended path.
COPY --from=builder /app/build /usr/share/nginx/html