# MQTT TLS Security Guide

## ⚠️ Sicherheitswarnung

**NIEMALS Port 1883 (unverschlüsseltes MQTT) nach außen öffnen!**

Port 1883 überträgt:
- ❌ Alle Daten im Klartext (Passwörter, Batteriedaten)
- ❌ Keine Authentifizierung standardmäßig
- ❌ Anfällig für Man-in-the-Middle Angriffe
- ❌ Ziel für IoT Botnets

**Risiko:** Kompromittierung innerhalb von Minuten bis Stunden

---

## ✅ Sichere Lösung: MQTT über TLS (Port 8883)

### Was ist TLS?

Transport Layer Security (TLS) ist die gleiche Verschlüsselung wie bei HTTPS:
- ✅ End-to-End Verschlüsselung (AES-256)
- ✅ Server-Authentifizierung (Zertifikate)
- ✅ Integritätsprüfung (keine Manipulation möglich)
- ✅ Passwort-Schutz zusätzlich

### Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                      HOME NETWORK                           │
│                                                             │
│  ┌──────────────┐      ┌──────────────────────────┐       │
│  │  Venus A     │      │   Raspberry Pi            │       │
│  │  UDP:30000   │◄─────│                           │       │
│  └──────────────┘      │   ┌──────────────────┐   │       │
│                        │   │ Venus Poller     │   │       │
│                        │   │ (unencrypted)    │   │       │
│                        │   └────────┬─────────┘   │       │
│                        │            ▼              │       │
│                        │   ┌──────────────────┐   │       │
│                        │   │ Mosquitto        │   │       │
│                        │   │                  │   │       │
│                        │   │ Port 1883 ───────┼───┼─► Local only
│                        │   │ (unencrypted)    │   │   (Docker network)
│                        │   │                  │   │
│                        │   │ Port 8883 ───────┼───┼─► Safe for internet
│                        │   │ (TLS encrypted)  │   │   (port forwarding)
│                        │   └──────────────────┘   │
│                        └──────────────────────────┘
│                                     │
└─────────────────────────────────────┼───────────────────────┘
                                      │
                     Port Forwarding  │ (8883 → Raspberry Pi)
                                      │
                          ┌───────────┴───────────┐
                          │                       │
                  ┌───────▼─────┐         ┌──────▼───────┐
                  │  Internet   │         │   Router     │
                  │  (TLS)      │         │  Firewall    │
                  └──────┬──────┘         └──────────────┘
                         │
                  ┌──────▼───────┐
                  │  Client App  │
                  │  (anywhere)  │
                  │              │
                  │  Needs:      │
                  │  - ca.crt    │
                  │  - username  │
                  │  - password  │
                  └──────────────┘
```

---

## 🚀 Setup-Anleitung

### Schritt 1: TLS-Zertifikate generieren

```bash
cd /home/ivan/AndroidStudioProjects/marstek-venus-bridge/mqtt-broker
chmod +x generate-certs.sh setup-tls.sh test-tls.sh
bash setup-tls.sh
```

**Was passiert:**
1. Erstellt CA (Certificate Authority) Zertifikat
2. Erstellt Server-Zertifikat (signiert von CA)
3. Optional: Client-Zertifikate für mutual TLS
4. Aktiviert TLS-Konfiguration

**Generierte Dateien:**
```
mqtt-broker/certs/
├── ca.crt          # CA Zertifikat (auf Clients installieren)
├── ca.key          # CA privater Schlüssel
├── server.crt      # Server Zertifikat
├── server.key      # Server privater Schlüssel
├── client.crt      # Client Zertifikat (optional)
└── client.key      # Client privater Schlüssel (optional)
```

### Schritt 2: Passwort erstellen

```bash
# Container neustarten (mit TLS-Konfiguration)
docker-compose restart mosquitto

# Passwort-Datei erstellen
docker exec -it venus-mqtt-broker mosquitto_passwd -c /mosquitto/config/passwordfile username

# Weiteren Benutzer hinzufügen (ohne -c flag)
docker exec -it venus-mqtt-broker mosquitto_passwd /mosquitto/config/passwordfile username2
```

**Wichtig:** Verwende ein starkes Passwort (mindestens 16 Zeichen)

### Schritt 3: TLS testen (lokal)

```bash
cd mqtt-broker
bash test-tls.sh
```

**Erwartete Ausgabe:**
```
Test 1: Local TLS connection (localhost:8883)...
✓ SUCCESS

Test 2: Unencrypted connection (localhost:1883)...
✓ SUCCESS

Test 3: Publish via TLS...
✓ SUCCESS
```

### Schritt 4: Port Forwarding (Router)

**Router-Konfiguration:**
1. Finde Raspberry Pi lokale IP: `hostname -I`
2. Router Admin-Interface öffnen (meist http://192.168.1.1)
3. Port Forwarding Regel hinzufügen:
   - **External Port:** 8883
   - **Internal IP:** `<Raspberry Pi IP>` (z.B. 192.168.1.100)
   - **Internal Port:** 8883
   - **Protocol:** TCP
4. Optional: Statische IP für Raspberry Pi (DHCP-Reservation)

**Wichtig:** Öffne NUR Port 8883, NIEMALS Port 1883!

### Schritt 5: Public IP herausfinden

```bash
curl ifconfig.me
```

Notiere die IP (z.B. 93.123.45.67) - das ist deine öffentliche Adresse.

### Schritt 6: Von außen testen

**Vom Smartphone/Laptop (NICHT im Home-WiFi):**

1. Kopiere `ca.crt` auf das Gerät:
   ```bash
   # Am Raspberry Pi
   cat /home/ivan/AndroidStudioProjects/marstek-venus-bridge/mqtt-broker/certs/ca.crt

   # Kopiere den Inhalt und speichere als ca.crt auf Smartphone
   ```

2. Teste Verbindung:
   ```bash
   mosquitto_sub -h 93.123.45.67 -p 8883 \
       --cafile ca.crt \
       -u username -P password \
       -t "marstek/#" -v
   ```

3. Erfolgreich wenn du die Batteriedaten siehst!

---

## 🔐 Sicherheits-Level

### Level 1: TLS + Passwort (Empfohlen)
**Was du hast:**
- ✅ Verschlüsselung (TLS 1.2+)
- ✅ Passwort-Authentifizierung
- ✅ Server-Verifizierung (ca.crt)

**Schutz gegen:**
- ✅ Sniffing/Lauschen
- ✅ Man-in-the-Middle
- ✅ Unbefugter Zugriff
- ✅ Botnet-Scans

**Anfällig für:**
- ⚠️ Gestohlene Credentials (wenn Passwort geleakt)

### Level 2: TLS + Passwort + Client-Zertifikate (Maximum)
**Zusätzlich:**
- ✅ Client muss Zertifikat haben (client.crt + client.key)
- ✅ Zwei-Faktor: Etwas was du weißt (Passwort) + etwas was du hast (Zertifikat)

**Schutz gegen:**
- ✅ Alles von Level 1
- ✅ Gestohlene Passwörter (Zertifikat fehlt)
- ✅ Brute-Force Angriffe

**Konfiguration:**
In `mosquitto-tls.conf` aktivieren:
```conf
require_certificate true
```

---

## 📱 Client-Integration (Android / Kotlin)

### Kotlin MQTT Client mit TLS

```kotlin
import org.eclipse.paho.client.mqttv3.*
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence
import java.io.InputStream
import java.security.KeyStore
import javax.net.ssl.*

class SecureMqttClient(
    private val serverUri: String,  // ssl://your-public-ip:8883
    private val username: String,
    private val password: String,
    private val caCertInputStream: InputStream  // ca.crt from assets
) {
    private var client: MqttClient? = null

    fun connect(onConnected: () -> Unit, onError: (Throwable) -> Unit) {
        try {
            // Load CA certificate
            val cf = CertificateFactory.getInstance("X.509")
            val ca = cf.generateCertificate(caCertInputStream)

            // Create TrustStore with CA
            val keyStore = KeyStore.getInstance(KeyStore.getDefaultType())
            keyStore.load(null, null)
            keyStore.setCertificateEntry("ca", ca)

            // Create TrustManager
            val tmf = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm())
            tmf.init(keyStore)

            // Create SSL Context
            val sslContext = SSLContext.getInstance("TLS")
            sslContext.init(null, tmf.trustManagers, null)

            // MQTT Connection Options
            val options = MqttConnectOptions().apply {
                socketFactory = sslContext.socketFactory
                userName = this@SecureMqttClient.username
                password = this@SecureMqttClient.password.toCharArray()
                isCleanSession = true
                connectionTimeout = 30
                keepAliveInterval = 60
                isAutomaticReconnect = true
            }

            // Connect
            client = MqttClient(serverUri, "wear-os-client", MemoryPersistence())
            client?.setCallback(object : MqttCallback {
                override fun connectionLost(cause: Throwable?) {
                    Log.e(TAG, "Connection lost", cause)
                }

                override fun messageArrived(topic: String?, message: MqttMessage?) {
                    // Handle incoming message
                    val data = message?.toString()
                    Log.d(TAG, "Received: $data")
                }

                override fun deliveryComplete(token: IMqttDeliveryToken?) {}
            })

            client?.connect(options)
            Log.i(TAG, "Connected to MQTT broker via TLS")
            onConnected()

        } catch (e: Exception) {
            Log.e(TAG, "MQTT connection failed", e)
            onError(e)
        }
    }

    fun subscribe(topic: String) {
        client?.subscribe(topic, 1)
    }

    fun disconnect() {
        client?.disconnect()
    }

    companion object {
        private const val TAG = "SecureMqttClient"
    }
}
```

### Android App Assets

1. Kopiere `ca.crt` nach `app/src/main/assets/ca.crt`

2. Verwendung:
```kotlin
val mqttClient = SecureMqttClient(
    serverUri = "ssl://93.123.45.67:8883",
    username = "marstek-user",
    password = "your-secure-password",
    caCertInputStream = assets.open("ca.crt")
)

mqttClient.connect(
    onConnected = {
        mqttClient.subscribe("marstek/venus/+/data")
    },
    onError = { error ->
        Log.e("MQTT", "Failed to connect", error)
    }
)
```

---

## 🛡️ Häufige Fragen

### Ist TLS so sicher wie HTTPS?
**Ja.** MQTT über TLS (Port 8883) nutzt die gleiche Verschlüsselung wie HTTPS:
- TLS 1.2 oder höher
- AES-256 Verschlüsselung
- Perfect Forward Secrecy

### Kann man den Traffic mitschneiden?
**Nein.** Selbst wenn jemand den Netzwerkverkehr aufzeichnet, sieht er nur verschlüsselte Daten.
Ohne den privaten Schlüssel (server.key) ist Entschlüsselung praktisch unmöglich.

### Was wenn jemand mein Passwort errät?
**Mit TLS + Passwort:** Er kann sich verbinden (wenn er auch ca.crt hat).
**Mit Client-Zertifikaten:** Passwort alleine reicht nicht, er braucht auch client.crt + client.key.

### Muss ich Let's Encrypt verwenden?
**Nein.** Self-signed Zertifikate sind für diesen Use-Case perfekt geeignet:
- Du kontrollierst beide Enden (Server + Client)
- Keine öffentliche Website, nur private API
- Kein Browser-Vertrauens-Check nötig

**Vorteile self-signed:**
- Kostenlos
- Keine externe Abhängigkeit
- Keine Erneuerung alle 90 Tage
- Kein DNS-Challenge nötig

### Wie oft Passwort ändern?
**Empfehlung:**
- Bei Verdacht auf Kompromittierung: Sofort
- Regulär: Alle 6-12 Monate
- Nach Geräteverlust (Smartphone): Sofort

---

## 📊 Performance

### Overhead von TLS

| Metrik | Unverschlüsselt | TLS |
|--------|----------------|-----|
| Handshake | ~1ms | ~50-100ms (nur bei Connect) |
| Pro Message | ~1ms | ~1-2ms |
| Datengröße | 100% | ~101% (minimaler Overhead) |
| CPU Last | ~1% | ~2-3% |

**Fazit:** TLS-Overhead ist vernachlässigbar bei 60s Poll-Interval.

---

## 🔧 Troubleshooting

### Fehler: "certificate verify failed"
**Ursache:** Client kann Server-Zertifikat nicht verifizieren.
**Lösung:** Prüfe ob ca.crt korrekt auf Client installiert ist.

### Fehler: "connection refused"
**Ursache:** Port Forwarding nicht korrekt oder Firewall blockiert.
**Lösung:**
```bash
# Am Raspberry Pi testen
sudo netstat -tlnp | grep 8883

# Von außen testen
telnet your-public-ip 8883
```

### Fehler: "authentication failed"
**Ursache:** Falsches Passwort oder Benutzer existiert nicht.
**Lösung:**
```bash
# Passwort neu setzen
docker exec -it venus-mqtt-broker mosquitto_passwd /mosquitto/config/passwordfile username
```

### Container startet nicht nach TLS-Setup
**Ursache:** Permissions auf Zertifikaten falsch.
**Lösung:**
```bash
cd mqtt-broker/certs
chmod 644 *.crt
chmod 600 *.key
docker-compose restart mosquitto
```

---

## ✅ Checkliste für Produktion

- [ ] TLS-Zertifikate generiert
- [ ] Starkes Passwort gesetzt (mindestens 16 Zeichen)
- [ ] Port 8883 im Router freigegeben
- [ ] Port 1883 NICHT nach außen exponiert
- [ ] ca.crt auf Client-Geräten installiert
- [ ] Verbindung von außen getestet
- [ ] Mosquitto Logs überwacht (keine Fehlversuche)
- [ ] Firewall-Regel für Rate-Limiting (optional)
- [ ] Client-Zertifikate für maximale Sicherheit (optional)

---

## 📚 Weiterführende Links

- [Mosquitto TLS Documentation](https://mosquitto.org/man/mosquitto-tls-7.html)
- [OWASP IoT Security](https://owasp.org/www-project-internet-of-things/)
- [Eclipse Paho MQTT Client](https://github.com/eclipse/paho.mqtt.android)
- [TLS Best Practices](https://wiki.mozilla.org/Security/Server_Side_TLS)

---

**Zusammenfassung:**

✅ **Port 8883 mit TLS + Passwort = Sicher für Internet-Zugriff**
❌ **Port 1883 ohne TLS = NIEMALS nach außen öffnen**

Die TLS-Konfiguration bietet Bank-Level Sicherheit für deine Batteriedaten.
