# Datalog de Temperatura • ESP32 + Flask + SQLite

Sistema simples de **IoT** para registrar (datalog) temperatura ambiente a cada 1 minuto:

- **API REST (Flask + SQLite)** para ingestão e consulta  
- **Dashboard Web** com gráfico atualizado automaticamente  
- **Simulador de ESP32** (gera leituras aleatórias para testes)  
- **Integração mínima ESP32 (Arduino IDE)**: envio via HTTP POST (JSON)

---

## Arquitetura

```
[ESP32 + DHT11] --Wi-Fi--> [API Flask]
                              |
                              v
                        [SQLite (datalog)]
                              |
                              v
                   [Dashboard Web (Chart.js)]
```

---

## Tecnologias

- Python 3.10+ • Flask  
- SQLite (módulo `sqlite3` embutido no Python)  
- Chart.js (front-end)  
- ESP32 (Arduino IDE) **ou** simulador em Python

---

## Estrutura do projeto

```
.
├── app.py                      # Inicialização da aplicação (app factory + run)
├── requirements.txt            # Dependências Python
├── simulator.py                # Simulador de ESP32 (gera leituras)
├── static/
│   └── index.html              # Dashboard (Chart.js)
└── src/
    ├── __init__.py             # create_app(), registra blueprints e DB
    ├── config.py               # Caminhos e constantes (STATIC_DIR, DB_PATH, etc.)
    ├── db.py                   # Conexão SQLite, schema e teardown
    ├── utils.py                # Helpers (tempo, ISO-8601, etc.)
    └── routes/
        ├── __init__.py         # Pacote de rotas
        ├── api.py              # Endpoints REST (/api/v1)
        └── web.py              # Rotas web (/, favicon)

```

> O arquivo `datalog.db` (SQLite) é criado automaticamente ao rodar `app.py`.

---

## Pré-requisitos

- **Python 3.10+**  
- (Opcional) utilitário `sqlite3` para inspecionar o banco pela linha de comando  
- Navegador moderno (Chrome/Edge/Firefox)

> Você **não precisa** instalar servidor de SQLite: o Python já vem com `sqlite3`.

---

## Instalação

1. Criar e ativar ambiente virtual
   - **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - **Linux/macOS (bash/zsh):**
     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```

2. Instalar dependências
   ```bash
   pip install -r requirements.txt
   ```

---

## Executando o servidor (API + Dashboard)

```bash
python app.py
```

Saída esperada (exemplo):
```
DB em: .../datalog.db
 * Running on http://127.0.0.1:5000
 * Running on http://SEU_IP_LOCAL:5000
```

- Dashboard (mesma máquina): **http://127.0.0.1:5000/**  
- Dashboard (outro dispositivo na mesma rede): **http://SEU_IP_LOCAL:5000/**

> Se o Windows pedir, **permita** o Python no firewall (rede Privada).

---

## Usando o simulador (opcional)

O simulador envia leituras **a cada 60s** no mesmo formato do ESP32 real:

```bash
python simulator.py --device-id ESP32_SIM --api http://127.0.0.1:5000 --interval 60
```

Parâmetros úteis:
- `--device-id` (padrão `ESP32_SIM`)
- `--api` (use `http://SEU_IP_LOCAL:5000` se for outro computador)
- `--interval` (segundos; padrão 60)
- `--print-only` (não envia, apenas imprime o JSON)

---

## Dashboard (gráfico em tempo real)

- Acesse **/** (raiz) do servidor:  
  - Mostra **temperatura atual** (KPI)  
  - **Gráfico** com as últimas leituras (agregado por minuto)  
  - **Botão “Exportar CSV”** para baixar todos os registros

Atualiza automaticamente (~10s). Leituras típicas: 1/min.

---

## Endpoints da API

**Saúde**
```
GET /api/v1/health
```

**Ingestão de leituras (principal)**
```
POST /api/v1/devices/<device_id>/readings
Content-Type: application/json
```

**Última leitura (global)**
```
GET /api/v1/readings/latest
```

**Série agregada (para o gráfico)**
```
GET /api/v1/readings/aggregate?limit=240
```

**Exportar CSV (todos os devices)**
```
GET /api/v1/export.csv
```

---

## Formato do JSON (exemplos)

### Envio (POST) do ESP32/simulador
```http
POST /api/v1/devices/ESP32_REAL/readings
Content-Type: application/json

{
  "temperature_c": 26.1,
  "humidity_percent": 55,
  "ts": "2025-08-12T14:41:40Z"   // opcional; se ausente, o servidor carimba
}
```

**Resposta (201/200)**
```json
{ "status": "ok", "device_id": "ESP32_REAL", "ts": "2025-08-12T14:41:40Z", "created": true }
```

---

## Integração mínima com ESP32 (Arduino IDE)

> **Objetivo:** Enviar um JSON via **HTTP POST** para o servidor Flask.  
> **Ajuste no seu sketch:** `WIFI_SSID`, `WIFI_PSW`, `SERVER_URL` (com **IP de quem roda o Flask**) e `DEVICE_ID`.

**Bibliotecas (Arduino IDE → Tools → Manage Libraries…)**
- *ESP32 boards* (by Espressif) — Boards Manager  
- *DHT sensor library* (by Adafruit) + *Adafruit Unified Sensor* (se for ler DHT11)

**Trechos essenciais (copiar e colar no seu sketch):**
```cpp
#include <WiFi.h>
#include <HTTPClient.h>

// ========= CONFIG =========
const char* WIFI_SSID  = "SEU_WIFI";
const char* WIFI_PSW   = "SUA_SENHA";
const char* SERVER_URL = "http://SEU_IP_LOCAL:5000"; // IP da máquina que roda o Flask
const char* DEVICE_ID  = "ESP32";
// ==========================

// Conecte ao Wi-Fi (chamar no setup e em caso de queda)
void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PSW);
  while (WiFi.status() != WL_CONNECTED) { delay(500); }
}

// Envie uma leitura (temperatura em °C, umidade em %)
bool postReading(float temperatureC, int humidityPercent) {
  String url = String(SERVER_URL) + "/api/v1/devices/" + DEVICE_ID + "/readings";
  String payload = String("{\"temperature_c\":") + String(temperatureC, 1) +
                   ",\"humidity_percent\":" + String(humidityPercent) + "}";

  HTTPClient http;
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  int code = http.POST((uint8_t*)payload.c_str(), payload.length());
  http.end();
  return (code > 0 && code < 400);
}
```

**Uso típico no seu `loop()` (exemplo conceitual):**
```cpp
// Exemplo: chame a cada 60s após ler seu sensor
// float t = dht.readTemperature(); // °C
// int   h = (int)round(dht.readHumidity());
// postReading(t, h);
```

> Dica: para carimbar horário no próprio ESP32, configure NTP e inclua `"ts":"<ISO8601Z>"` no payload. Se não incluir, o servidor registra o horário de chegada.

---

## Acesso pela rede (outro computador / ESP32)

- Descubra o IP do PC que roda o Flask: `ipconfig` (Windows) / `ifconfig` (Linux/macOS).  
- Use **`http://SEU_IP_LOCAL:5000`** no navegador e no ESP32.  
- Abra/permita a **porta 5000** no firewall local, se necessário.  
- Prefira todos os dispositivos na **mesma rede Wi-Fi** (laboratório).

---

## Banco de dados (SQLite)

- Arquivo: `datalog.db` (criado automaticamente)  
- Tabela: `readings` (índice por `device_id, ts`, com `UNIQUE(device_id, ts)` para evitar duplicatas)

**Inspeção rápida (opcional)**
```bash
sqlite3 datalog.db
.tables
SELECT COUNT(*) FROM readings;
SELECT * FROM readings ORDER BY ts DESC LIMIT 5;
.quit
```

> Para “zerar” o banco, pare o servidor e **apague** `datalog.db`.

---

## Solução de problemas

- **Dashboard abre, mas não plota**  
  - Verifique `GET /api/v1/readings/latest` (deve retornar algo).  
  - Confirme que o ESP32/simulador está fazendo **POST 201** no endpoint.

- **ESP32 não envia**  
  - Confira **SSID/senha** e **SERVER_URL** com IP correto.  
  - Teste do PC:  
    ```bash
    curl http://SEU_IP_LOCAL:5000/api/v1/health
    ```

- **Porta 5000 bloqueada**  
  - Libere no firewall ou altere a porta no `app.py`:
    ```python
    app.run(host="0.0.0.0", port=8080, debug=True)
    ```

- **`sqlite3` ausente no Python (raro)**  
  - Reinstale o Python **ou**:
    ```bash
    pip install pysqlite3-binary
    ```
    E, no topo do `app.py`:
    ```python
    try:
        import sqlite3
    except Exception:
        import pysqlite3 as sqlite3
    ```

