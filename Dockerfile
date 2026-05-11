FROM node:22-alpine AS frontend-build
WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build



FROM eclipse-temurin:17-jdk AS build
WORKDIR /app

COPY mvnw mvnw
COPY .mvn .mvn
COPY pom.xml pom.xml
COPY src src
COPY --from=frontend-build /frontend/dist src/main/resources/static

RUN chmod +x mvnw && ./mvnw -q -DskipTests package

FROM eclipse-temurin:17-jre
WORKDIR /app

COPY --from=build /app/target/*.jar app.jar

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]

#FROM python:3.12-slim
#
#WORKDIR /bot
#COPY vk_bot/requirements.txt ./requirements.txt
#RUN pip install --no-cache-dir -r requirements.txt
#COPY vk_bot/ ./
#
#CMD ["python", "vk_bot.py"]

# FROM python:3.12-slim

# WORKDIR /bot

# COPY tg_bot.py /bot/tg_bot.py
# COPY requirements.txt /bot/requirements.txt

# RUN pip install --no-cache-dir -r requirements.txt

# CMD ["python", "tg_bot.py"]
