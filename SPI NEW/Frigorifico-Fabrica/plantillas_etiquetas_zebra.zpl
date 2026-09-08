; ============================================================================
; SISTEMA DE PRODUCCIÓN INTEGRAL (SPI) - PLANTILLAS OFICIALES ZEBRA ZPL-II
; Medidas: 100x75mm (Canal), 100x50mm (Bachada), 75x50mm (Decomiso)
; Resolución: 203 DPI (8 dots/mm)
; ============================================================================

; ----------------------------------------------------------------------------
; 1. ETIQUETA MEDIA RES / CANAL FRIGORÍFICO (100 mm x 75 mm = 812 x 609 dots)
; Variables a reemplazar: 
; {{LOTE_MEDIA_RES}}, {{TROPA_DTE}}, {{LADO}}, {{KILOS}}, {{GRASA_MM}}, 
; {{MAGRO_PCT}}, {{FECHA_HORA}}, {{OPERARIO_ID}}, {{URL_QR}}
; ----------------------------------------------------------------------------
^XA
^PW812
^LL609
^CF0,30
^FO50,40^FD*** SISTEMA DE PRODUCCION INTEGRAL (SPI) ***^FS
^FO50,80^GB712,3,3^FS
^CF0,42
^FO50,105^FDLOTE MEDIA RES:^FS
^CF0,55
^FO50,155^FD{{LOTE_MEDIA_RES}}^FS
^CF0,34
^FO50,230^FDTROPA DT-e: {{TROPA_DTE}}^FS
^FO50,275^FDPESO GANCHO: {{KILOS}} kg  [LADO: {{LADO}}]^FS
^FO50,320^FDTIP: GRASA {{GRASA_MM}}mm | MAGRO {{MAGRO_PCT}}%^FS
^FO50,365^FDFECHA: {{FECHA_HORA}}  OP: {{OPERARIO_ID}}^FS
^BY3,2,80
^FO50,420^BCN,80,Y,N,N^FD{{LOTE_MEDIA_RES}}^FS
^FO620,400^BQN,2,5^FDQA,{{URL_QR}}^FS
^XZ

; ----------------------------------------------------------------------------
; 2. ETIQUETA BACHADA FÁBRICA DE CHACINADOS (100 mm x 50 mm = 812 x 406 dots)
; Variables a reemplazar:
; {{NOMBRE_PRODUCTO}}, {{LOTE_BACHADA}}, {{KILOS}}, {{UNIDADES}}, 
; {{LOTE_TOCINO}}, {{FECHA_ELAB}}
; ----------------------------------------------------------------------------
^XA
^PW812
^LL406
^CF0,28
^FO40,30^FDSPI - FABRICA DE CHACINADOS^FS
^FO40,65^GB732,2,2^FS
^CF0,38
^FO40,85^FD{{NOMBRE_PRODUCTO}}^FS
^CF0,48
^FO40,135^FDLOTE: {{LOTE_BACHADA}}^FS
^CF0,30
^FO40,195^FDPESO: {{KILOS}} kg | UNIDADES: {{UNIDADES}} un^FS
^FO40,235^FDTOCINO: LOTE {{LOTE_TOCINO}} | ELAB: {{FECHA_ELAB}}^FS
^BY2,2,65
^FO40,285^BCN,65,Y,N,N^FD{{LOTE_BACHADA}}^FS
^XZ

; ----------------------------------------------------------------------------
; 3. ETIQUETA DECOMISO SANITARIO SENASA (75 mm x 50 mm = 609 x 406 dots)
; Variables a reemplazar:
; {{TROPA_DTE}}, {{MOTIVO_DECOMISO}}, {{DESTINO_SCRAP}}, {{VETERINARIO_SENASA}}, 
; {{FECHA_HORA}}
; ----------------------------------------------------------------------------
^XA
^PW609
^LL406
^CF0,32
^FO30,30^FD[!] DECOMISO SANITARIO SENASA [!]^FS
^FO30,70^GB550,3,3^FS
^CF0,30
^FO30,95^FDTROPA ORIGEN: {{TROPA_DTE}}^FS
^CF0,34
^FO30,140^FDMOTIVO: {{MOTIVO_DECOMISO}}^FS
^CF0,30
^FO30,195^FDDESTINO: {{DESTINO_SCRAP}}^FS
^FO30,240^FDFECHA: {{FECHA_HORA}}^FS
^FO30,280^FDVET. SENASA: {{VETERINARIO_SENASA}}^FS
^FO30,330^GB550,40,40,W,0^FS
^CF0,28
^FO50,338^FDNO APTO CONSUMO HUMANO - DESNATURALIZADO^FS
^XZ
