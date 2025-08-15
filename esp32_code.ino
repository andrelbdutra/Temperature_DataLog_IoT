#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"
#include <time.h>

#define DHTPIN 14
#define DHTTYPE DHT11

//Pro horário
const char* ntpServer = "pool.ntp.org";
const long  gmtOffset_sec = -3;     // UTC -3
const int   daylightOffset_sec = 0;

//Credenciais WiFi
const char* ssid = "nome"; //nome do wifi
const char* password = "senha"; //senha do wi-fi

//endereço do WebService
String serverName = "https://preencher/aqui";

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200); //para mostrar mensagens no Serial Monitor
  delay(1000);

  // Conectar ao Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Conectando ao WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi conectado!");
  Serial.print("IP Local: ");
  Serial.println(WiFi.localIP());

  // Configura NTP
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  struct tm timeinfo;
  if(!getLocalTime(&timeinfo)){
      Serial.println("Falha ao obter hora via NTP");
      return;
  }
  Serial.println(&timeinfo, "Hora atual: %Y-%m-%d %H:%M:%S");

  dht.begin();
}

String getIsoTime() { //gera timestamps dinâmicos com a hora atual
  time_t now;
  struct tm timeinfo;
  time(&now);
  gmtime_r(&now, &timeinfo);
  char buf[25];
  strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
  return String(buf);
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    float t = dht.readTemperature();
    if (isnan(t)) {
      Serial.println("Falha ao ler do sensor DHT!");
      delay(10000);
      return;
    }
    Serial.print("Temperatura lida: ");
    Serial.println(t, 1);

    HTTPClient http;
    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");

    String jsonPayload = "{\"ts\": \"" + getIsoTime() + "\", \"temperature_c\": " + String(t, 1) + "}";

    Serial.println("Enviando HTTP POST...");
    int httpResponseCode = http.POST(jsonPayload);

    if (httpResponseCode > 0) {
      Serial.print("HTTP Response code: ");
      Serial.println(httpResponseCode);
      Serial.println(http.getString());
    } else {
      Serial.print("Erro na requisição: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  } else {
    Serial.println("WiFi desconectado!");
  }

  delay(60000); //Envia a cada 60 segundos
}
