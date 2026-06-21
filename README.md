# Etiquetas de validade — MY-7779

App web pra impressora térmica BLE **Baihuo MY-7779**. Gera etiquetas 5×5cm com a
data de fabricação (grid 2×5 ou 2×7) e imprime direto via **Web Bluetooth**.

## Uso (iPhone)

Abra a página no app **Bluefy** (o Safari não tem Web Bluetooth):

- Escolha o modelo, a data e o tamanho da fonte
- Toque em **Imprimir** → selecione **MY-7779**

## Arquivos

- `index.html` — o app (canvas + Web Bluetooth), servido pelo GitHub Pages
- `labels.py` — versão Python (testes/preview no Mac, via `bleak` + Pillow)
- `discover.py` / `inspect_gatt.py` / `calib.py` / `print_test.py` — scripts de descoberta do protocolo

## Protocolo (descoberto)

ESC/POS sobre BLE. Serviço `000018f0…`, característica de escrita `00002af1…`.
Raster `GS v 0`. Etiqueta = 384×400 dots (5×5cm).
