import React, { useState, useEffect, useRef } from 'react';
import Tesseract from 'tesseract.js';
import './App.css';

// Configuración de locales disponibles
const LOCALES = ['Local 1', 'Local 2', 'Local 3'];

// Datos demostrativos de transformaciones despiece por local
const SAMPLE_YIELD_DATA = [
  { Sucursal: "Local comercial 1", "Fecha/Hora": "28/07/2026 09:30", Operario: "Marcos G.", "Lote Madre": "280726-1", "Corte Madre": "CARRE", "Peso Madre (KG)": 45.50, "Lote Resultante": "3280726001", "Producto Resultante": "COSTELETA", "Peso Resultante (KG)": 41.80, "Rendimiento (%)": "91.87%", "Merma Registrada (KG)": 3.70, "Merma (%)": "8.13%" },
  { Sucursal: "Local comercial 1", "Fecha/Hora": "28/07/2026 10:15", Operario: "Marcos G.", "Lote Madre": "280726-2", "Corte Madre": "PALETA", "Peso Madre (KG)": 38.20, "Lote Resultante": "3280726002", "Producto Resultante": "CHULETA DE PALETA", "Peso Resultante (KG)": 35.10, "Rendimiento (%)": "91.88%", "Merma Registrada (KG)": 3.10, "Merma (%)": "8.12%" },
  { Sucursal: "Local comercial 2", "Fecha/Hora": "27/07/2026 11:00", Operario: "Gonzalo P.", "Lote Madre": "270726-1", "Corte Madre": "JAMON", "Peso Madre (KG)": 52.00, "Lote Resultante": "2270726001", "Producto Resultante": "CHULETA DE JAMÓN", "Peso Resultante (KG)": 48.60, "Rendimiento (%)": "93.46%", "Merma Registrada (KG)": 3.40, "Merma (%)": "6.54%" },
  { Sucursal: "Local comercial 2", "Fecha/Hora": "27/07/2026 14:20", Operario: "Gonzalo P.", "Lote Madre": "270726-2", "Corte Madre": "PECHITO C-M", "Peso Madre (KG)": 29.80, "Lote Resultante": "2270726002", "Producto Resultante": "COSTILLA", "Peso Resultante (KG)": 27.20, "Rendimiento (%)": "91.28%", "Merma Registrada (KG)": 2.60, "Merma (%)": "8.72%" },
  { Sucursal: "Local comercial 3", "Fecha/Hora": "26/07/2026 08:45", Operario: "Lucas R.", "Lote Madre": "260726-1", "Corte Madre": "BONDIOLA S-H", "Peso Madre (KG)": 22.40, "Lote Resultante": "1260726001", "Producto Resultante": "CHURRASCO DE BONDIOLA", "Peso Resultante (KG)": 20.80, "Rendimiento (%)": "92.86%", "Merma Registrada (KG)": 1.60, "Merma (%)": "7.14%" },
  { Sucursal: "Local comercial 3", "Fecha/Hora": "26/07/2026 10:50", Operario: "Lucas R.", "Lote Madre": "260726-2", "Corte Madre": "LOMO", "Peso Madre (KG)": 14.30, "Lote Resultante": "1260726002", "Producto Resultante": "BIFE DE LOMO", "Peso Resultante (KG)": 13.50, "Rendimiento (%)": "94.41%", "Merma Registrada (KG)": 0.80, "Merma (%)": "5.59%" },
  { Sucursal: "Local comercial 1", "Fecha/Hora": "25/07/2026 16:10", Operario: "Marcos G.", "Lote Madre": "250726-1", "Corte Madre": "BLANDA", "Peso Madre (KG)": 34.00, "Lote Resultante": "3250726001", "Producto Resultante": "PICADA ESPECIAL", "Peso Resultante (KG)": 31.90, "Rendimiento (%)": "93.82%", "Merma Registrada (KG)": 2.10, "Merma (%)": "6.18%" },
  { Sucursal: "Local comercial 2", "Fecha/Hora": "24/07/2026 12:30", Operario: "Gonzalo P.", "Lote Madre": "240726-1", "Corte Madre": "PULPA DE PALETA", "Peso Madre (KG)": 26.50, "Lote Resultante": "2240726001", "Producto Resultante": "PULPA DE PALETA", "Peso Resultante (KG)": 24.80, "Rendimiento (%)": "93.58%", "Merma Registrada (KG)": 1.70, "Merma (%)": "6.42%" },
];

// --- ICONOS CON ESTÉTICA ROBÓTICA / FUTURISTA ---
const IconHome = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ display: 'inline-block', verticalAlign: 'middle' }}>
    <rect x="3" y="3" width="18" height="18" rx="3" strokeWidth="2.5" />
    <path d="M7 9h10M7 13h10M7 17h6" strokeWidth="2" strokeOpacity="0.8" />
    <path d="M17 17v-4" strokeWidth="2" strokeLinecap="square" />
    <circle cx="17" cy="17" r="1.5" fill="currentColor" />
  </svg>
);

const IconConsistency = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ display: 'inline-block', verticalAlign: 'middle' }}>
    <path d="M3 21h18M3 3v18" strokeWidth="2.5" />
    <rect x="6" y="11" width="3" height="7" rx="1" strokeWidth="2" />
    <rect x="11" y="7" width="3" height="11" rx="1" strokeWidth="2" />
    <rect x="16" y="13" width="3" height="5" rx="1" strokeWidth="2" />
    <path d="M2 9h20" stroke="#ef4444" strokeWidth="1.5" strokeDasharray="3 3" />
    <circle cx="7.5" cy="11" r="1" fill="currentColor" />
    <circle cx="12.5" cy="7" r="1" fill="currentColor" />
    <circle cx="17.5" cy="13" r="1" fill="currentColor" />
  </svg>
);

const IconYield = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ display: 'inline-block', verticalAlign: 'middle' }}>
    {/* Estructura de engranaje cibernético y corte preciso */}
    <circle cx="12" cy="12" r="9" strokeWidth="2" strokeDasharray="4 2" />
    <circle cx="12" cy="12" r="4" strokeWidth="2" />
    <path d="M12 2v6M12 16v6M2 12h6M16 12h6" strokeWidth="2" />
    <path d="M6 6l4 4M14 14l4 4" strokeWidth="2" />
  </svg>
);

const IconImport = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ display: 'inline-block', verticalAlign: 'middle' }}>
    <rect x="5" y="8" width="14" height="12" rx="2" strokeWidth="2.5" />
    <path d="M9 4v4M15 4v4" strokeWidth="2.5" />
    <path d="M12 11v5m0 0l-3-3m3 3l3-3" strokeWidth="2" />
    <circle cx="9" cy="17" r="1" fill="currentColor" />
    <circle cx="15" cy="17" r="1" fill="currentColor" />
  </svg>
);

const IconGear = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ display: 'inline-block', verticalAlign: 'middle', marginRight: 6 }}>
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
);

const IconRefresh = ({ size = 16, isLoading = false }) => (
  <svg 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2.5" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    className={isLoading ? "spin-icon" : ""}
    style={{ display: 'inline-block', verticalAlign: 'middle', marginRight: 6 }}
  >
    <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
  </svg>
);

function App() {
  // --- Estados de Autenticación ---
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [operator, setOperator] = useState('');
  const [pin, setPin] = useState('');
  const [loginError, setLoginError] = useState('');
  const [isLoadingLogin, setIsLoadingLogin] = useState(false);

  // --- Estados de Formulario de Stock ---
  const [local, setLocal] = useState('Local 1');
  const [corteInput, setCorteInput] = useState('');
  const [corteSeleccionado, setCorteSeleccionado] = useState(null);
  const [peso, setPeso] = useState('');
  const [lote, setLote] = useState('');
  const [fecha, setFecha] = useState('');
  const [cortesList, setCortesList] = useState([]);
  const [filteredCortes, setFilteredCortes] = useState([]);
  const [showCortesDropdown, setShowCortesDropdown] = useState(false);
  const [isLoadingSubmit, setIsLoadingSubmit] = useState(false);

  // --- Estado de la Tabla de Sesión Local ---
  const [sessionRecords, setSessionRecords] = useState([]);

  // --- Estados del Escáner OCR ---
  const [showCamera, setShowCamera] = useState(false);
  const [cameraState, setCameraState] = useState('stream'); // 'stream' | 'processing' | 'result'
  const [ocrStatus, setOcrStatus] = useState('');
  const [capturedImageSrc, setCapturedImageSrc] = useState(null);
  
  // Resultados temporales en el Modal OCR
  const [ocrCorte, setOcrCorte] = useState(null);
  const [ocrCorteInput, setOcrCorteInput] = useState('');
  const [ocrLote, setOcrLote] = useState('');
  const [ocrPeso, setOcrPeso] = useState('');
  const [ocrFilteredCortes, setOcrFilteredCortes] = useState([]);
  const [showOcrCorteDropdown, setShowOcrCorteDropdown] = useState(false);

  // --- Sistema de Notificaciones (Toasts) ---
  const [toast, setToast] = useState(null);

  // --- Estados de Reportes ---
  const [activeTab, setActiveTab] = useState('rendimiento'); // 'rendimiento' (Transformaciones) | 'consistencia' | 'importar'
  
  // Consistencia
  const [consistencyData, setConsistencyData] = useState([]);
  const [isLoadingConsistency, setIsLoadingConsistency] = useState(false);
  const [filterConsistencySucursal, setFilterConsistencySucursal] = useState('Todas');
  const [filterConsistencySearch, setFilterConsistencySearch] = useState('');
  const [filterConsistencyDateFrom, setFilterConsistencyDateFrom] = useState('');
  const [filterConsistencyDateTo, setFilterConsistencyDateTo] = useState('');
  
  // Rendimiento
  const [yieldData, setYieldData] = useState(SAMPLE_YIELD_DATA);
  const [isLoadingYield, setIsLoadingYield] = useState(false);
  const [filterYieldSucursal, setFilterYieldSucursal] = useState('Todas');
  const [filterYieldMotherCut, setFilterYieldMotherCut] = useState('Todos');
  const [filterYieldSearch, setFilterYieldSearch] = useState('');
  const [filterYieldDateFrom, setFilterYieldDateFrom] = useState('');
  const [filterYieldDateTo, setFilterYieldDateTo] = useState('');
  
  // Importador
  const [tangoFile, setTangoFile] = useState(null);
  const [tangoRows, setTangoRows] = useState([]);
  const [isUploadingTango, setIsUploadingTango] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  // Column visibility toggles
  const CONSISTENCY_COLUMNS = [
    { key: 'Sucursal', label: 'Sucursal', default: true },
    { key: 'Código', label: 'Código', default: true },
    { key: 'Producto', label: 'Producto', default: true },
    { key: 'Inicial', label: 'Inicial', default: true },
    { key: 'REI', label: 'REI (Tango)', default: true },
    { key: 'Ventas', label: 'Ventas (REM)', default: true },
    { key: 'Ajustes', label: 'Ajustes', default: false },
    { key: 'EntrDespiece', label: 'Entr. Despiece', default: true },
    { key: 'SalDespiece', label: 'Sal. Despiece', default: true },
    { key: 'Teorico', label: 'Teórico', default: true },
    { key: 'Conteo', label: 'Conteo', default: true },
    { key: 'Diferencia', label: 'Diferencia', default: true },
    { key: 'Estado', label: 'Estado', default: true },
  ];
  const YIELD_COLUMNS = [
    { key: 'Sucursal', label: 'Sucursal', default: true },
    { key: 'FechaHora', label: 'Fecha/Hora', default: true },
    { key: 'Operario', label: 'Operario', default: true },
    { key: 'CorteMadre', label: 'Corte Madre', default: true },
    { key: 'PesoMadre', label: 'Peso Madre', default: true },
    { key: 'Lote', label: 'Lote', default: false },
    { key: 'Resultante', label: 'Resultante', default: true },
    { key: 'PesoRes', label: 'Peso Res.', default: true },
    { key: 'RendPct', label: 'Rend. %', default: true },
    { key: 'MermaKG', label: 'Merma KG', default: true },
    { key: 'MermaPct', label: 'Merma %', default: true },
  ];
  const [consistencyVisibleCols, setConsistencyVisibleCols] = useState(
    () => Object.fromEntries(CONSISTENCY_COLUMNS.map(c => [c.key, c.default]))
  );
  const [yieldVisibleCols, setYieldVisibleCols] = useState(
    () => Object.fromEntries(YIELD_COLUMNS.map(c => [c.key, c.default]))
  );
  const [showConsistencyColMenu, setShowConsistencyColMenu] = useState(false);
  const [showYieldColMenu, setShowYieldColMenu] = useState(false);

  // --- Efecto para cargar datos de los reportes al cambiar de pestaña ---
  useEffect(() => {
    if (!isLoggedIn) return;
    if (activeTab !== 'rendimiento') {
      setActiveTab('rendimiento');
    } else {
      fetchYieldData();
    }
  }, [activeTab, isLoggedIn]);

  const fetchConsistencyData = async () => {
    setIsLoadingConsistency(true);
    try {
      const res = await fetch('/api/stock/reporte-consistencia');
      if (res.ok) {
        const data = await res.json();
        setConsistencyData(data);
      } else {
        showToast('error', 'Error al obtener consistencia de stock.');
      }
    } catch (e) {
      showToast('error', 'Error de conexión con el servidor.');
    } finally {
      setIsLoadingConsistency(false);
    }
  };

  const fetchYieldData = async () => {
    setIsLoadingYield(true);
    try {
      const res = await fetch('/api/stock/reporte-rendimiento');
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          setYieldData(data);
        } else {
          setYieldData(SAMPLE_YIELD_DATA);
        }
      } else {
        setYieldData(SAMPLE_YIELD_DATA);
      }
    } catch (e) {
      setYieldData(SAMPLE_YIELD_DATA);
    } finally {
      setIsLoadingYield(false);
    }
  };

  // --- Lógica del Importador de Tango (CSV Semicolón) ---
  const handleTangoFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      processTangoFile(file);
    }
  };

  const processTangoFile = (file) => {
    setTangoFile(file);
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target.result;
      const lines = text.split(/\r?\n/);
      if (lines.length <= 1) {
        showToast('error', 'El archivo está vacío o no contiene suficientes filas.');
        return;
      }
      
      // Parsear cabecera para mapear columnas
      const headers = lines[0].split(';').map(h => h.trim().replace(/^"|"$/g, ''));
      const rows = [];
      
      for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;
        
        const cols = line.split(';').map(c => c.trim().replace(/^"|"$/g, ''));
        if (cols.length < headers.length) continue;
        
        const rowObj = {};
        headers.forEach((h, idx) => {
          rowObj[h] = cols[idx];
        });
        
        // Validar cantidad
        if (rowObj['Cantidad control stock']) {
          rowObj['Cantidad control stock'] = parseFloat(rowObj['Cantidad control stock'].replace(',', '.'));
        }
        
        rows.push(rowObj);
      }
      
      setTangoRows(rows);
      showToast('success', `Archivo leído. Se encontraron ${rows.length} registros.`);
    };
    reader.readAsText(file, 'utf-8');
  };

  const handleUploadTangoToSheets = async () => {
    if (tangoRows.length === 0) {
      showToast('error', 'No hay datos cargados para enviar.');
      return;
    }
    
    setIsUploadingTango(true);
    try {
      const res = await fetch('/api/stock/save-tango', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rows: tangoRows })
      });
      
      if (res.ok) {
        showToast('success', `¡Éxito! Se importaron ${tangoRows.length} registros en RTANGOSTOCK y se recalcularon los reportes.`);
        setTangoFile(null);
        setTangoRows([]);
      } else {
        const errorData = await res.json();
        showToast('error', errorData.detail || 'Error al importar los datos.');
      }
    } catch (e) {
      showToast('error', 'Error de red. No se pudo conectar con el servidor.');
    } finally {
      setIsUploadingTango(false);
    }
  };

  // --- Referencias ---
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const cortesListRef = useRef([]);

  // Autologin si ya existe la sesión en localStorage
  useEffect(() => {
    const savedOp = localStorage.getItem('spi_stock_operator');
    if (savedOp) {
      setOperator(savedOp);
      setIsLoggedIn(true);
      setActiveTab('home');
    }
    // Establecer fecha de hoy por defecto
    const today = new Date().toISOString().split('T')[0];
    setFecha(today);
    
    // Cargar cortes desde la API
    fetchCortes();
  }, []);

  // Sincronizar cortesList con la referencia
  useEffect(() => {
    cortesListRef.current = cortesList;
  }, [cortesList]);

  // Cargar cortes desde la API del servidor
  const fetchCortes = async () => {
    try {
      const res = await fetch('/api/stock/cortes');
      if (res.ok) {
        const data = await res.json();
        setCortesList(data);
      }
    } catch (e) {
      showToast('error', 'Error al cargar cortes desde el servidor.');
    }
  };

  // Filtrar cortes del formulario principal
  useEffect(() => {
    if (!corteInput.trim()) {
      setFilteredCortes([]);
      return;
    }
    const cleanInput = normalizeText(corteInput);
    const filtered = cortesList.filter(c => 
      normalizeText(c.descripcion).includes(cleanInput) || 
      c.codigo.includes(cleanInput)
    );
    setFilteredCortes(filtered.slice(0, 15));
  }, [corteInput, cortesList]);

  // Filtrar cortes del formulario temporal dentro del modal OCR
  useEffect(() => {
    if (!ocrCorteInput.trim()) {
      setOcrFilteredCortes([]);
      return;
    }
    const cleanInput = normalizeText(ocrCorteInput);
    const filtered = cortesList.filter(c => 
      normalizeText(c.descripcion).includes(cleanInput) || 
      c.codigo.includes(cleanInput)
    );
    setOcrFilteredCortes(filtered.slice(0, 15));
  }, [ocrCorteInput, cortesList]);

  // Mostrar Toast temporario
  const showToast = (type, message) => {
    setToast({ type, message });
    setTimeout(() => {
      setToast(null);
    }, 4000);
  };

  // Normalizar texto para comparación sin acentos ni mayúsculas
  const normalizeText = (text) => {
    if (!text) return '';
    return text.toString().normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
  };

  // --- Lógica de Login ---
  const handlePinPress = (num) => {
    if (pin.length < 6) {
      setPin(prev => prev + num);
    }
  };

  const handlePinDelete = () => {
    setPin(prev => prev.slice(0, -1));
  };

  const handlePinClear = () => {
    setPin('');
  };

  const handleLoginSubmit = async (e) => {
    if (e) e.preventDefault();
    if (pin.length < 4) {
      setLoginError('El PIN debe tener al menos 4 dígitos.');
      return;
    }

    setIsLoadingLogin(true);
    setLoginError('');

    try {
      const res = await fetch('/api/stock/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pin })
      });

      const data = await res.json();
      if (res.ok) {
        setOperator(data.usuario);
        localStorage.setItem('spi_stock_operator', data.usuario);
        setIsLoggedIn(true);
        setActiveTab('rendimiento');
        setPin('');
        showToast('success', `¡Bienvenido, ${data.usuario}!`);
      } else {
        setLoginError(data.detail || 'PIN Incorrecto.');
        setPin('');
      }
    } catch (err) {
      setLoginError('Error de conexión con el servidor.');
    } finally {
      setIsLoadingLogin(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('spi_stock_operator');
    setOperator('');
    setIsLoggedIn(false);
    setActiveTab('rendimiento');
    showToast('success', 'Sesión cerrada.');
  };

  // --- Lógica del Escáner OCR por Captura Manual ---
  const startCamera = async () => {
    setCameraState('stream');
    setOcrCorte(null);
    setOcrCorteInput('');
    setOcrLote('');
    setOcrPeso('');
    setCapturedImageSrc(null);
    setOcrStatus('Alinee la etiqueta dentro del recuadro y presione CAPTURAR.');
    setShowCamera(true);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
    } catch (err) {
      console.error(err);
      setOcrStatus('Error al acceder a la cámara. Verifique los permisos.');
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    setShowCamera(false);
    setCameraState('stream');
    setOcrStatus('');
    setCapturedImageSrc(null);
  };

  // Capturar frame actual, pausar video e iniciar Tesseract
  const captureFrameAndProcess = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    const width = video.videoWidth;
    const height = video.videoHeight;
    canvas.width = width;
    canvas.height = height;

    // Dibujar fotograma del video
    ctx.drawImage(video, 0, 0, width, height);

    // Calcular recuadro de alineación central (Formato vertical)
    const boxW = Math.floor(width * 0.70);
    const boxH = Math.floor(height * 0.75);
    const boxX = Math.floor((width - boxW) / 2);
    const boxY = Math.floor((height - boxH) / 2);

    // Canvas recortado original en color
    const croppedCanvas = document.createElement('canvas');
    croppedCanvas.width = boxW;
    croppedCanvas.height = boxH;
    const croppedCtx = croppedCanvas.getContext('2d');
    croppedCtx.drawImage(canvas, boxX, boxY, boxW, boxH, 0, 0, boxW, boxH);

    // Canvas de baja resolución para Gemini (480x640)
    const targetW = 480;
    const targetH = 640;
    const geminiCanvas = document.createElement('canvas');
    geminiCanvas.width = targetW;
    geminiCanvas.height = targetH;
    const geminiCtx = geminiCanvas.getContext('2d');
    geminiCtx.drawImage(croppedCanvas, 0, 0, boxW, boxH, 0, 0, targetW, targetH);

    // Generar imagen JPEG comprimida a 70% (20-30KB) en color natural para Gemini
    const colorDataUrl = geminiCanvas.toDataURL('image/jpeg', 0.7);
    
    setCapturedImageSrc(colorDataUrl);
    setCameraState('processing');
    setOcrStatus('Analizando etiqueta con Gemini IA...');

    // Pausar flujo de video físico
    video.pause();

    try {
      // Intentar primero con la API de Gemini (Multimodal en Backend)
      const res = await fetch('/api/stock/gemini-ocr', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: colorDataUrl })
      });

      if (res.ok) {
        const data = await res.json();
        
        // Buscar el objeto corte basándonos en la descripción devuelta
        let matchedCorte = null;
        if (data.corte) {
          const cleanName = normalizeText(data.corte);
          matchedCorte = cortesListRef.current.find(c => 
            normalizeText(c.descripcion).includes(cleanName) || 
            cleanName.includes(normalizeText(c.descripcion))
          );
        }
        
        setOcrCorte(matchedCorte);
        setOcrCorteInput(matchedCorte ? matchedCorte.descripcion : (data.corte || ''));
        setOcrLote(data.lote ? data.lote.toString() : '');
        setOcrPeso(data.peso ? data.peso.toString() : '');
        
        setCameraState('result');
        setOcrStatus('Lectura con Gemini completada. Verifique y confirme.');
        
        if (navigator.vibrate) {
          navigator.vibrate(100);
        }
      } else {
        const errorData = await res.json().catch(() => ({ detail: '' }));
        console.warn("Fallo Gemini API, usando local:", errorData.detail);
        showToast('error', 'Falta API Key de Gemini. Usando lector local...');
        runLocalTesseract(croppedCanvas);
      }
    } catch (err) {
      console.warn("Error de red con Gemini, usando local:", err);
      showToast('error', 'Error de red. Usando lector local...');
      runLocalTesseract(croppedCanvas);
    }
  };

  // Lector local de respaldo (Tesseract.js)
  const runLocalTesseract = async (croppedCanvas) => {
    setOcrStatus('Analizando con lector local... Espere un momento.');
    try {
      const boxW = croppedCanvas.width;
      const boxH = croppedCanvas.height;

      // Crear canvas temporal para binarizar para Tesseract
      const binarizedCanvas = document.createElement('canvas');
      binarizedCanvas.width = boxW;
      binarizedCanvas.height = boxH;
      const binarizedCtx = binarizedCanvas.getContext('2d');
      binarizedCtx.drawImage(croppedCanvas, 0, 0);

      // Procesamiento blanco y negro + contraste
      const imgData = binarizedCtx.getImageData(0, 0, boxW, boxH);
      const data = imgData.data;
      for (let i = 0; i < data.length; i += 4) {
        const r = data[i];
        const g = data[i+1];
        const b = data[i+2];
        const gray = 0.299 * r + 0.587 * g + 0.114 * b;
        const val = gray > 115 ? 255 : 0;
        data[i] = val;
        data[i+1] = val;
        data[i+2] = val;
      }
      binarizedCtx.putImageData(imgData, 0, 0);
      const binarizedDataUrl = binarizedCanvas.toDataURL('image/jpeg');

      const result = await Tesseract.recognize(binarizedDataUrl, 'eng');
      const text = result.data.text;
      const parsed = parseEtiquetaText(text);
      
      setOcrCorte(parsed.corte);
      setOcrCorteInput(parsed.corte ? parsed.corte.descripcion : '');
      setOcrLote(parsed.lote);
      setOcrPeso(parsed.peso);
      
      setCameraState('result');
      if (parsed.corte && parsed.lote && parsed.peso) {
        setOcrStatus('Lectura local exitosa. Verifique los datos.');
      } else {
        setOcrStatus('Lectura local parcial. Complete los campos faltantes.');
      }
      
      if (navigator.vibrate) {
        navigator.vibrate(100);
      }
    } catch (e) {
      console.error(e);
      setOcrStatus('Error al leer el texto localmente. Intente tomar la foto de nuevo.');
      setCameraState('result');
    }
  };

  // Reanudar cámara para una nueva captura
  const retryCapture = () => {
    setOcrCorte(null);
    setOcrCorteInput('');
    setOcrLote('');
    setOcrPeso('');
    setCapturedImageSrc(null);
    setCameraState('stream');
    setOcrStatus('Alinee la etiqueta dentro del recuadro y presione CAPTURAR.');
    if (videoRef.current) {
      videoRef.current.play();
    }
  };

  // Confirmar y registrar en la tabla temporal local
  const confirmOcrData = () => {
    if (!ocrCorte) {
      showToast('error', 'Por favor seleccione un corte válido.');
      return;
    }
    if (!ocrPeso || parseFloat(ocrPeso) <= 0) {
      showToast('error', 'Por favor ingrese un peso válido mayor a 0.');
      return;
    }
    if (!ocrLote.trim()) {
      showToast('error', 'Por favor ingrese el número de lote.');
      return;
    }

    const newRecord = {
      id: Date.now(),
      codigo: ocrCorte.codigo,
      descripcion: ocrCorte.descripcion,
      peso: parseFloat(ocrPeso),
      lote: ocrLote.trim()
    };

    // Verificar duplicado en la sesión
    const isDuplicate = sessionRecords.some(r => r.lote === newRecord.lote && r.peso === newRecord.peso && r.codigo === newRecord.codigo);
    if (isDuplicate) {
      showToast('error', '¡Advertencia! Este bulto ya está en la tabla de resumen.');
    }

    setSessionRecords(prev => [newRecord, ...prev]);
    showToast('success', 'Registro agregado a la sesión.');
    stopCamera();
  };

  // Algoritmo de parseo de texto de etiqueta capturada
  const parseEtiquetaText = (text) => {
    const lines = text.split('\n').map(l => l.toUpperCase().trim()).filter(l => l.length > 0);
    console.log("Captured OCR Lines:", lines);

    let detectedCorte = null;
    let detectedLote = '';
    let detectedPeso = '';

    // 1. Detección de Corte
    for (const line of lines) {
      const cleanLine = normalizeText(line);
      if (cleanLine.length < 3) continue;

      const match = cortesListRef.current.find(c => {
        const cleanDesc = normalizeText(c.descripcion);
        if (cleanDesc.length < 4) return false;
        return cleanLine.includes(cleanDesc) || cleanDesc.includes(cleanLine);
      });
      if (match) {
        detectedCorte = match;
        break;
      }
    }

    // 2. Detección de Lote
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (line.includes('LOTE') || line.includes('LOT')) {
        const numbersInLine = line.match(/\b\d{6,11}\b/);
        if (numbersInLine) {
          detectedLote = numbersInLine[0];
        } else if (i + 1 < lines.length) {
          const nextLine = lines[i + 1];
          const numbersNext = nextLine.match(/\b\d{6,11}\b/);
          if (numbersNext) {
            detectedLote = numbersNext[0];
          }
        }
      }
    }
    if (!detectedLote) {
      for (const line of lines) {
        const matchLongNum = line.match(/\b\d{8,11}\b/);
        if (matchLongNum) {
          detectedLote = matchLongNum[0];
          break;
        }
      }
    }

    // 3. Detección de Peso
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (line.includes('KILOS') || line.includes('KILO') || line.includes('KGS') || line.includes('KG')) {
        const decInLine = line.match(/\b\d+[\.,]\d+\b/);
        if (decInLine) {
          detectedPeso = decInLine[0].replace(',', '.');
        } else if (i + 1 < lines.length) {
          const nextLine = lines[i + 1];
          const decNext = nextLine.match(/\b\d+[\.,]\d+\b/);
          if (decNext) {
            detectedPeso = decNext[0].replace(',', '.');
          } else {
            const intNext = nextLine.match(/\b\d+\b/);
            if (intNext) {
              detectedPeso = intNext[0];
            }
          }
        }
      }
    }
    if (!detectedPeso) {
      for (const line of lines) {
        const decMatch = line.match(/\b\d+[\.,]\d+\b/);
        if (decMatch) {
          detectedPeso = decMatch[0].replace(',', '.');
          break;
        }
      }
    }

    return { corte: detectedCorte, lote: detectedLote, peso: detectedPeso };
  };

  // --- Carga Manual: Agregar a la tabla de sesión ---
  const handleAddManualRecord = (e) => {
    e.preventDefault();

    if (!corteSeleccionado) {
      showToast('error', 'Por favor seleccione un corte válido.');
      return;
    }
    if (!peso || parseFloat(peso) <= 0) {
      showToast('error', 'Por favor ingrese un peso válido mayor a 0.');
      return;
    }
    if (!lote.trim()) {
      showToast('error', 'Por favor ingrese el número de lote.');
      return;
    }

    const newRecord = {
      id: Date.now(),
      codigo: corteSeleccionado.codigo,
      descripcion: corteSeleccionado.descripcion,
      peso: parseFloat(peso),
      lote: lote.trim()
    };

    // Verificar duplicado en la sesión
    const isDuplicate = sessionRecords.some(r => r.lote === newRecord.lote && r.peso === newRecord.peso && r.codigo === newRecord.codigo);
    if (isDuplicate) {
      showToast('error', '¡Advertencia! Este bulto ya está en la tabla de resumen.');
    }

    setSessionRecords(prev => [newRecord, ...prev]);
    showToast('success', 'Registro agregado a la sesión.');
    
    // Limpiar campos del formulario principal
    setCorteInput('');
    setCorteSeleccionado(null);
    setPeso('');
    setLote('');
  };

  // Eliminar un registro individual de la sesión
  const handleDeleteSessionRecord = (id) => {
    setSessionRecords(prev => prev.filter(r => r.id !== id));
    showToast('success', 'Registro removido de la sesión.');
  };

  // Enviar el lote consolidado a Google Sheets
  const handleSendBatchToSheets = async () => {
    if (sessionRecords.length === 0) {
      showToast('error', 'No hay registros en la sesión para enviar.');
      return;
    }
    if (!fecha) {
      showToast('error', 'Por favor seleccione la fecha de control.');
      return;
    }

    setIsLoadingSubmit(true);

    const payload = {
      local,
      fecha: formatDateToSheets(fecha),
      operario: operator,
      registros: sessionRecords.map(r => ({
        codigo: r.codigo,
        descripcion: r.descripcion,
        peso: r.peso,
        lote: r.lote
      }))
    };

    try {
      const res = await fetch('/api/stock/registrar-lote', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (res.ok) {
        showToast('success', `¡Éxito! Se registraron ${sessionRecords.length} bultos correctamente.`);
        setSessionRecords([]); // Limpiar la tabla de sesión
      } else {
        showToast('error', data.detail || 'Error al guardar el lote.');
      }
    } catch (err) {
      showToast('error', 'Error de red. No se pudo conectar con el servidor.');
    } finally {
      setIsLoadingSubmit(false);
    }
  };

  // Convertir fecha de YYYY-MM-DD a DD/MM/YYYY
  const formatDateToSheets = (dateStr) => {
    if (!dateStr) return '';
    const parts = dateStr.split('-');
    if (parts.length === 3) {
      return `${parts[2]}/${parts[1]}/${parts[0]}`;
    }
    return dateStr;
  };

  // Seleccionar sugerencia
  const selectCorte = (c) => {
    setCorteSeleccionado(c);
    setCorteInput(c.descripcion);
    setShowCortesDropdown(false);
  };

  const selectOcrCorte = (c) => {
    setOcrCorte(c);
    setOcrCorteInput(c.descripcion);
    setShowOcrCorteDropdown(false);
  };

  return (
    <div className="app-container">
      {/* Toast Alert */}
      {toast && (
        <div className={`toast-alert toast-${toast.type}`}>
          <span className="toast-icon">{toast.type === 'success' ? '✓' : '⚠'}</span>
          <span className="toast-message">{toast.message}</span>
        </div>
      )}

      {/* PANTALLA 1: LOGIN POR PIN */}
      {!isLoggedIn ? (
        <div className="login-card-container">
          <div className="login-card glass">
            <div className="brand-header">
              <img src="Logo cerdos MINI.png" alt="Logo" className="brand-logo" />
              <h1>SPI - Control de Stock</h1>
              <p>Ingrese su PIN de operador para comenzar</p>
            </div>

            <form onSubmit={handleLoginSubmit} className="login-form">
              <div className="pin-display-wrapper">
                <input
                  type="password"
                  value={pin}
                  readOnly
                  placeholder="******"
                  className="pin-input-field"
                />
              </div>

              {loginError && <p className="login-error-message">{loginError}</p>}

              {/* Numpad táctil */}
              <div className="numpad-grid">
                {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(num => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => handlePinPress(num)}
                    className="numpad-btn"
                  >
                    {num}
                  </button>
                ))}
                <button type="button" onClick={handlePinClear} className="numpad-btn action-btn font-sm">
                  Borrar
                </button>
                <button type="button" onClick={() => handlePinPress(0)} className="numpad-btn">
                  0
                </button>
                <button type="button" onClick={handlePinDelete} className="numpad-btn action-btn">
                  ⌫
                </button>
              </div>

              <button
                type="submit"
                disabled={isLoadingLogin || pin.length < 4}
                className="btn-submit btn-login"
              >
                {isLoadingLogin ? 'Verificando...' : 'INGRESAR'}
              </button>
            </form>
          </div>
        </div>
      ) : (
        /* PANTALLA 2: DASHBOARD DE ESCRITORIO */
        <div className="desktop-dashboard">
          
          {/* SIDEBAR NAVIGATION */}
          <aside className="sidebar glass">
            <div className="sidebar-brand">
              <img src="Logo cerdos MINI.png" alt="Logo" className="sidebar-logo" />
              <h3 className="sidebar-title">SPI Stock</h3>
            </div>

            <nav className="sidebar-nav">
              <button 
                onClick={() => setActiveTab('rendimiento')} 
                className={`sidebar-link ${activeTab === 'rendimiento' ? 'active' : ''}`}
              >
                <span className="sidebar-icon"><IconYield size={18} /></span> Transformaciones
              </button>
            </nav>

            <div className="sidebar-footer">
              <div className="sidebar-user">
                <span className="user-avatar">{operator.charAt(0).toUpperCase()}</span>
                <span className="user-name">{operator}</span>
              </div>
              <button onClick={handleLogout} className="btn-sidebar-logout">Salir</button>
            </div>
          </aside>

          {/* MAIN CONTENT */}
          <div className="main-content">

            {/* VISTA 0: PORTAL / HOME */}
            {activeTab === 'home' && (
              <div className="portal-home fade-in">
                <div className="portal-welcome">
                  <h2 className="portal-title">Hola, {operator.split(' ')[0]}</h2>
                  <p className="portal-subtitle">Seleccioná el módulo con el que deseas operar</p>
                </div>

                <div className="portal-grid">
                  <div onClick={() => setActiveTab('consistencia')} className="portal-card glass">
                    <div className="portal-card-icon" style={{ background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)' }}>
                      <IconConsistency size={28} />
                    </div>
                    <div className="portal-card-body">
                      <h3>Consistencia de Stock</h3>
                      <p>Auditoría en tiempo real: sobrantes, faltantes y desvíos por sucursal y producto.</p>
                    </div>
                    <span className="portal-card-arrow">→</span>
                  </div>
                  <div onClick={() => setActiveTab('rendimiento')} className="portal-card glass">
                    <div className="portal-card-icon" style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}>
                      <IconYield size={28} />
                    </div>
                    <div className="portal-card-body">
                      <h3>Rendimiento de Despiece</h3>
                      <p>Análisis de rendimientos y mermas por sesión de despostado y operario.</p>
                    </div>
                    <span className="portal-card-arrow">→</span>
                  </div>
                  <div onClick={() => setActiveTab('importar')} className="portal-card glass">
                    <div className="portal-card-icon" style={{ background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' }}>
                      <IconImport size={28} />
                    </div>
                    <div className="portal-card-body">
                      <h3>Importar Movimientos de Tango</h3>
                      <p>Subí el archivo CSV del ERP para recalcular todos los análisis automáticamente.</p>
                    </div>
                    <span className="portal-card-arrow">→</span>
                  </div>
                </div>
              </div>
            )}

            {/* VISTA 2: CONSISTENCIA DE STOCK */}
            {activeTab === 'consistencia' && (
              <div className="report-card glass fade-in">
                <div className="report-header">
                  <h3>Consistencia de Stock</h3>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <div style={{ position: 'relative' }}>
                      <button onClick={() => setShowConsistencyColMenu(!showConsistencyColMenu)} className="btn-refresh">
                        <IconGear /> Columnas
                      </button>
                      {showConsistencyColMenu && (
                        <div className="col-menu glass">
                          {CONSISTENCY_COLUMNS.map(c => (
                            <label key={c.key} className="col-menu-item">
                              <input type="checkbox" checked={consistencyVisibleCols[c.key]} onChange={() => setConsistencyVisibleCols(prev => ({ ...prev, [c.key]: !prev[c.key] }))} />
                              {c.label}
                            </label>
                          ))}
                        </div>
                      )}
                    </div>
                    <button onClick={fetchConsistencyData} disabled={isLoadingConsistency} className="btn-refresh">
                      <IconRefresh isLoading={isLoadingConsistency} /> Recargar
                    </button>
                  </div>
                </div>

                {/* Filtros */}
                <div className="filters-panel glass">
                  <div className="form-group">
                    <label>Sucursal</label>
                    <select value={filterConsistencySucursal} onChange={(e) => setFilterConsistencySucursal(e.target.value)} className="form-control select-control">
                      <option value="Todas">Todas las sucursales</option>
                      <option value="Local comercial 1">Local Comercial 1</option>
                      <option value="Local comercial 2">Local Comercial 2</option>
                      <option value="Local comercial 3">Local Comercial 3</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Desde</label>
                    <input type="date" value={filterConsistencyDateFrom} onChange={(e) => setFilterConsistencyDateFrom(e.target.value)} className="form-control text-control" />
                  </div>
                  <div className="form-group">
                    <label>Hasta</label>
                    <input type="date" value={filterConsistencyDateTo} onChange={(e) => setFilterConsistencyDateTo(e.target.value)} className="form-control text-control" />
                  </div>
                  <div className="form-group">
                    <label>Buscar Producto</label>
                    <input type="text" value={filterConsistencySearch} onChange={(e) => setFilterConsistencySearch(e.target.value)} placeholder="Nombre o código..." className="form-control text-control" />
                  </div>
                </div>

                {/* Tabla de Consistencia */}
                {isLoadingConsistency ? (
                  <div style={{ padding: '60px 0', textAlign: 'center' }}>
                    <div className="spinner-mini" style={{ width: '40px', height: '40px', borderColor: 'rgba(99,102,241,0.2)', borderTopColor: 'var(--primary-color)', margin: '0 auto' }}></div>
                    <p style={{ marginTop: 16, color: 'var(--text-secondary)' }}>Cargando datos...</p>
                  </div>
                ) : (
                  <div className="report-table-responsive">
                    <table className="report-table">
                      <thead>
                        <tr>
                          {consistencyVisibleCols.Sucursal && <th>Sucursal</th>}
                          {consistencyVisibleCols.Código && <th>Código</th>}
                          {consistencyVisibleCols.Producto && <th>Producto</th>}
                          {consistencyVisibleCols.Inicial && <th className="text-right">Inicial</th>}
                          {consistencyVisibleCols.REI && <th className="text-right">REI</th>}
                          {consistencyVisibleCols.Ventas && <th className="text-right">Ventas</th>}
                          {consistencyVisibleCols.Ajustes && <th className="text-right">Ajustes</th>}
                          {consistencyVisibleCols.EntrDespiece && <th className="text-right">Entr. Desp.</th>}
                          {consistencyVisibleCols.SalDespiece && <th className="text-right">Sal. Desp.</th>}
                          {consistencyVisibleCols.Teorico && <th className="text-right">Teórico</th>}
                          {consistencyVisibleCols.Conteo && <th className="text-right">Conteo</th>}
                          {consistencyVisibleCols.Diferencia && <th className="text-right">Diferencia</th>}
                          {consistencyVisibleCols.Estado && <th className="text-center">Estado</th>}
                        </tr>
                      </thead>
                      <tbody>
                        {consistencyData
                          .filter(r => {
                            const matchSuc = filterConsistencySucursal === 'Todas' || r.Sucursal === filterConsistencySucursal;
                            const matchSearch = !filterConsistencySearch || 
                              r.Producto.toLowerCase().includes(filterConsistencySearch.toLowerCase()) ||
                              r.Código.toString().includes(filterConsistencySearch);
                            let matchDate = true;
                            if (r.Fecha && (filterConsistencyDateFrom || filterConsistencyDateTo)) {
                              const rowDate = r.Fecha;
                              if (filterConsistencyDateFrom && rowDate < filterConsistencyDateFrom) matchDate = false;
                              if (filterConsistencyDateTo && rowDate > filterConsistencyDateTo) matchDate = false;
                            }
                            return matchSuc && matchSearch && matchDate;
                          })
                          .map((r, idx) => (
                            <tr key={idx}>
                              {consistencyVisibleCols.Sucursal && <td>{r.Sucursal}</td>}
                              {consistencyVisibleCols.Código && <td>{r.Código}</td>}
                              {consistencyVisibleCols.Producto && <td className="font-semibold">{r.Producto}</td>}
                              {consistencyVisibleCols.Inicial && <td className="text-right">{parseFloat(r['Stock Inicial'] || 0).toFixed(2)}</td>}
                              {consistencyVisibleCols.REI && <td className="text-right text-success">{parseFloat(r['Ingresos (Tango REI)'] || 0).toFixed(2)}</td>}
                              {consistencyVisibleCols.Ventas && <td className="text-right" style={{ color: '#f87171' }}>{parseFloat(r['Ventas (Tango REM)'] || 0).toFixed(2)}</td>}
                              {consistencyVisibleCols.Ajustes && <td className="text-right">{parseFloat(r['Ajustes (Tango DEC/DON)'] || 0).toFixed(2)}</td>}
                              {consistencyVisibleCols.EntrDespiece && <td className="text-right text-success">{parseFloat(r['Transf. Entradas (Despiece)'] || 0).toFixed(2)}</td>}
                              {consistencyVisibleCols.SalDespiece && <td className="text-right" style={{ color: '#f87171' }}>{parseFloat(r['Transf. Salidas (Despiece)'] || 0).toFixed(2)}</td>}
                              {consistencyVisibleCols.Teorico && <td className="text-right font-semibold">{parseFloat(r['Stock Teórico'] || 0).toFixed(2)}</td>}
                              {consistencyVisibleCols.Conteo && <td className="text-right font-semibold">{r['Stock Físico Real'] !== "" ? parseFloat(r['Stock Físico Real']).toFixed(2) : '-'}</td>}
                              {consistencyVisibleCols.Diferencia && <td className={`text-right font-bold ${r.Diferencia < 0 ? 'text-danger' : r.Diferencia > 0 ? 'text-warning' : ''}`}>{r.Diferencia !== "" ? parseFloat(r.Diferencia).toFixed(2) : '-'}</td>}
                              {consistencyVisibleCols.Estado && <td className="text-center"><span className={`badge-status ${r.Estado.toLowerCase().replace(' ', '-')}`}>{r.Estado}</span></td>}
                            </tr>
                          ))
                        }
                        {consistencyData.length === 0 && (
                          <tr>
                            <td colSpan="13" style={{ padding: '30px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                              No hay datos disponibles. Presione Recargar.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* VISTA 3: DASHBOARD DE TRANSFORMACIONES Y RENDIMIENTO POR LOCAL */}
            {activeTab === 'rendimiento' && (
              <div className="transform-dashboard-wrapper fade-in">
                
                {/* HEADLINE & ACTION CONTROLS */}
                <div className="transform-header-panel glass">
                  <div>
                    <h2 className="transform-main-title">Dashboard de Transformaciones por Local</h2>
                    <p className="transform-main-subtitle">Análisis ejecutivo de volumen procesado, rendimiento de cortes madre y mermas por sucursal</p>
                  </div>
                  <div className="transform-header-actions">
                    <div style={{ position: 'relative' }}>
                      <button onClick={() => setShowYieldColMenu(!showYieldColMenu)} className="btn-refresh">
                        <IconGear /> Columnas
                      </button>
                      {showYieldColMenu && (
                        <div className="col-menu glass">
                          {YIELD_COLUMNS.map(c => (
                            <label key={c.key} className="col-menu-item">
                              <input type="checkbox" checked={yieldVisibleCols[c.key]} onChange={() => setYieldVisibleCols(prev => ({ ...prev, [c.key]: !prev[c.key] }))} />
                              {c.label}
                            </label>
                          ))}
                        </div>
                      )}
                    </div>
                    <button onClick={fetchYieldData} disabled={isLoadingYield} className="btn-refresh btn-primary-glow">
                      <IconRefresh isLoading={isLoadingYield} /> Sincronizar Datos
                    </button>
                  </div>
                </div>

                {/* FILTROS INTERACTIVOS & ACCESOS RÁPIDOS */}
                <div className="filters-panel glass transform-filters-container">
                  <div className="form-group">
                    <label>Sucursal / Local</label>
                    <select value={filterYieldSucursal} onChange={(e) => setFilterYieldSucursal(e.target.value)} className="form-control select-control">
                      <option value="Todas">Todas las sucursales</option>
                      <option value="Local comercial 1">Local Comercial 1</option>
                      <option value="Local comercial 2">Local Comercial 2</option>
                      <option value="Local comercial 3">Local Comercial 3</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Corte Madre (Origen)</label>
                    <select value={filterYieldMotherCut} onChange={(e) => setFilterYieldMotherCut(e.target.value)} className="form-control select-control">
                      <option value="Todos">Todos los cortes madre</option>
                      {Array.from(new Set(yieldData.map(r => r['Corte Madre'] || ''))).filter(c => c).map(c => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Buscar Resultante</label>
                    <input type="text" value={filterYieldSearch} onChange={(e) => setFilterYieldSearch(e.target.value)} placeholder="Ej: Costeleta, Bife..." className="form-control text-control" />
                  </div>

                  <div className="form-group">
                    <label>Desde</label>
                    <input type="date" value={filterYieldDateFrom} onChange={(e) => setFilterYieldDateFrom(e.target.value)} className="form-control text-control" />
                  </div>

                  <div className="form-group">
                    <label>Hasta</label>
                    <input type="date" value={filterYieldDateTo} onChange={(e) => setFilterYieldDateTo(e.target.value)} className="form-control text-control" />
                  </div>

                  <div className="form-group span-full-presets">
                    <label>Segmento de Fechas Rápido</label>
                    <div className="date-presets-row">
                      <button type="button" onClick={() => { setFilterYieldDateFrom(''); setFilterYieldDateTo(''); }} className={`preset-pill ${!filterYieldDateFrom && !filterYieldDateTo ? 'active' : ''}`}>Todo</button>
                      <button type="button" onClick={() => { const today = new Date().toISOString().split('T')[0]; setFilterYieldDateFrom(today); setFilterYieldDateTo(today); }} className="preset-pill">Hoy</button>
                      <button type="button" onClick={() => { const today = new Date(); const past = new Date(); past.setDate(today.getDate()-7); setFilterYieldDateFrom(past.toISOString().split('T')[0]); setFilterYieldDateTo(today.toISOString().split('T')[0]); }} className="preset-pill">Últimos 7 Días</button>
                      <button type="button" onClick={() => { const today = new Date(); const startMonth = new Date(today.getFullYear(), today.getMonth(), 1); setFilterYieldDateFrom(startMonth.toISOString().split('T')[0]); setFilterYieldDateTo(today.toISOString().split('T')[0]); }} className="preset-pill">Este Mes</button>
                    </div>
                  </div>
                </div>

                {/* COMPUTED METRICS CALCULATION */}
                {(() => {
                  const normalizeStore = (name) => {
                    if (!name) return '';
                    const str = name.toString().toLowerCase().trim();
                    if (str.includes('local 1') || str.includes('comercial 1') || str.endsWith('1')) return 'Local comercial 1';
                    if (str.includes('local 2') || str.includes('comercial 2') || str.endsWith('2')) return 'Local comercial 2';
                    if (str.includes('local 3') || str.includes('comercial 3') || str.endsWith('3')) return 'Local comercial 3';
                    return name.toString().trim();
                  };

                  const parseRowDateToISO = (rawStr) => {
                    if (!rawStr) return '';
                    const str = rawStr.toString().trim().split(' ')[0];
                    if (str.includes('/')) {
                      const parts = str.split('/');
                      if (parts.length === 3) {
                        let day = parts[0].padStart(2, '0');
                        let month = parts[1].padStart(2, '0');
                        let year = parts[2].trim();
                        if (year.length === 2) year = '20' + year;
                        return `${year}-${month}-${day}`;
                      }
                    } else if (str.includes('-')) {
                      const parts = str.split('-');
                      if (parts.length === 3) {
                        if (parts[0].length === 4) {
                          return `${parts[0]}-${parts[1].padStart(2, '0')}-${parts[2].padStart(2, '0')}`;
                        } else {
                          let day = parts[0].padStart(2, '0');
                          let month = parts[1].padStart(2, '0');
                          let year = parts[2].trim();
                          if (year.length === 2) year = '20' + year;
                          return `${year}-${month}-${day}`;
                        }
                      }
                    }
                    return str;
                  };

                  const filteredYieldList = yieldData.filter(r => {
                    const normSuc = normalizeStore(r.Sucursal);
                    const normFilterSuc = normalizeStore(filterYieldSucursal);
                    const matchSuc = filterYieldSucursal === 'Todas' || normSuc === normFilterSuc;
                    const matchMother = filterYieldMotherCut === 'Todos' || r['Corte Madre'] === filterYieldMotherCut;
                    const matchSearch = !filterYieldSearch || 
                      (r['Producto Resultante'] && r['Producto Resultante'].toLowerCase().includes(filterYieldSearch.toLowerCase())) ||
                      (r['Corte Madre'] && r['Corte Madre'].toLowerCase().includes(filterYieldSearch.toLowerCase()));
                    
                    let matchDate = true;
                    if (r['Fecha/Hora'] && (filterYieldDateFrom || filterYieldDateTo)) {
                      const rowDate = parseRowDateToISO(r['Fecha/Hora']);
                      if (rowDate) {
                        if (filterYieldDateFrom && rowDate < filterYieldDateFrom) matchDate = false;
                        if (filterYieldDateTo && rowDate > filterYieldDateTo) matchDate = false;
                      }
                    }
                    return matchSuc && matchMother && matchSearch && matchDate;
                  });

                  // 1. Salidas (Resultantes): Suma de todas las filas resultantes de producto
                  const totalResultante = filteredYieldList.reduce((a, r) => a + parseFloat(r['Peso Resultante (KG)'] || 0), 0);

                  // 2. Entradas (Madre) y Mermas: Deduplicación por Sesión Única de Despiece
                  const globalSessionsMap = new Map();
                  filteredYieldList.forEach(r => {
                    const normSuc = normalizeStore(r.Sucursal);
                    const sessionKey = `${normSuc}_${r['Fecha/Hora']}_${r.Operario}_${r['Lote Madre']}_${r['Corte Madre']}`;
                    if (!globalSessionsMap.has(sessionKey)) {
                      globalSessionsMap.set(sessionKey, {
                        madre: parseFloat(r['Peso Madre (KG)'] || 0),
                        merma: parseFloat(r['Merma Registrada (KG)'] || 0)
                      });
                    }
                  });

                  let totalMadre = 0;
                  let totalMerma = 0;
                  globalSessionsMap.forEach(sess => {
                    totalMadre += sess.madre;
                    totalMerma += sess.merma;
                  });

                  const rendGlobal = totalMadre > 0 ? ((totalResultante / totalMadre) * 100).toFixed(2) : '0.00';
                  const mermaPctGlobal = totalMadre > 0 ? ((totalMerma / totalMadre) * 100).toFixed(2) : '0.00';

                  // 3. Breakdown por Sucursal con Deduplicación Correcta
                  const storeList = ['Local comercial 1', 'Local comercial 2', 'Local comercial 3'].map(suc => {
                    const normTarget = normalizeStore(suc);
                    const rowsInStore = filteredYieldList.filter(r => normalizeStore(r.Sucursal) === normTarget);
                    const resSum = rowsInStore.reduce((a, r) => a + parseFloat(r['Peso Resultante (KG)'] || 0), 0);
                    
                    const storeSessionsMap = new Map();
                    rowsInStore.forEach(r => {
                      const sKey = `${r['Fecha/Hora']}_${r.Operario}_${r['Lote Madre']}_${r['Corte Madre']}`;
                      if (!storeSessionsMap.has(sKey)) {
                        storeSessionsMap.set(sKey, {
                          madre: parseFloat(r['Peso Madre (KG)'] || 0),
                          merma: parseFloat(r['Merma Registrada (KG)'] || 0)
                        });
                      }
                    });

                    let madreSum = 0;
                    let mermaSum = 0;
                    storeSessionsMap.forEach(s => {
                      madreSum += s.madre;
                      mermaSum += s.merma;
                    });

                    const rend = madreSum > 0 ? ((resSum / madreSum) * 100).toFixed(1) : '0.0';
                    return { 
                      name: suc, 
                      madre: madreSum, 
                      res: resSum, 
                      merma: mermaSum, 
                      count: storeSessionsMap.size, 
                      rend 
                    };
                  });

                  // 4. Breakdown por Corte Madre con Deduplicación Correcta
                  const motherCuts = Array.from(new Set(yieldData.map(r => r['Corte Madre'] || ''))).filter(Boolean);
                  const cutList = motherCuts.map(cut => {
                    const rowsInCut = filteredYieldList.filter(r => r['Corte Madre'] === cut);
                    const resSum = rowsInCut.reduce((a, r) => a + parseFloat(r['Peso Resultante (KG)'] || 0), 0);

                    const cutSessionsMap = new Map();
                    rowsInCut.forEach(r => {
                      const normSuc = normalizeStore(r.Sucursal);
                      const sKey = `${normSuc}_${r['Fecha/Hora']}_${r.Operario}_${r['Lote Madre']}_${cut}`;
                      if (!cutSessionsMap.has(sKey)) {
                        cutSessionsMap.set(sKey, {
                          madre: parseFloat(r['Peso Madre (KG)'] || 0),
                          merma: parseFloat(r['Merma Registrada (KG)'] || 0)
                        });
                      }
                    });

                    let madreSum = 0;
                    let mermaSum = 0;
                    cutSessionsMap.forEach(s => {
                      madreSum += s.madre;
                      mermaSum += s.merma;
                    });

                    const rend = madreSum > 0 ? ((resSum / madreSum) * 100).toFixed(1) : '0.0';
                    return { 
                      name: cut, 
                      madre: madreSum, 
                      res: resSum, 
                      merma: mermaSum, 
                      count: cutSessionsMap.size, 
                      rend 
                    };
                  }).sort((a, b) => b.madre - a.madre);

                  return (
                    <>
                      {/* TARJETAS KPI DE ALTO IMPACTO */}
                      <div className="transform-kpi-grid">
                        <div className="transform-kpi-card glass kpi-indigo">
                          <div className="kpi-icon-badge">🥩</div>
                          <div className="kpi-info">
                            <span className="kpi-label">Materia Prima Procesada</span>
                            <h3 className="kpi-value">{totalMadre.toFixed(2)} <span className="unit">KG</span></h3>
                            <span className="kpi-subtext">Cortes madre ingresados a despiece</span>
                          </div>
                        </div>

                        <div className="transform-kpi-card glass kpi-emerald">
                          <div className="kpi-icon-badge">🔪</div>
                          <div className="kpi-info">
                            <span className="kpi-label">Producto Resultante Obtenido</span>
                            <h3 className="kpi-value">{totalResultante.toFixed(2)} <span className="unit">KG</span></h3>
                            <span className="kpi-subtext">Cortes listos para comercializar</span>
                          </div>
                        </div>

                        <div className="transform-kpi-card glass kpi-cyan">
                          <div className="kpi-icon-badge">📈</div>
                          <div className="kpi-info">
                            <span className="kpi-label">Rendimiento Promedio</span>
                            <h3 className="kpi-value">{rendGlobal}%</h3>
                            <div className="kpi-progress-bar">
                              <div className="kpi-progress-fill" style={{ width: `${Math.min(parseFloat(rendGlobal), 100)}%` }}></div>
                            </div>
                            <span className="kpi-subtext">Eficiencia global de conversión</span>
                          </div>
                        </div>

                        <div className="transform-kpi-card glass kpi-amber">
                          <div className="kpi-icon-badge">⚠️</div>
                          <div className="kpi-info">
                            <span className="kpi-label">Merma & Descarte</span>
                            <h3 className="kpi-value">{totalMerma.toFixed(2)} <span className="unit">KG</span></h3>
                            <span className="kpi-subtext" style={{ color: '#f87171' }}>{mermaPctGlobal}% de pérdida del peso total</span>
                          </div>
                        </div>
                      </div>

                      {/* SECCIÓN 1: COMPARATIVA DE TRANSFORMACIONES POR SUCURSAL / LOCAL */}
                      <div className="transform-section-header">
                        <h3>🏢 Eficiencia de Transformación por Local Comercial</h3>
                        <p>Comparativa de volumen procesado, salidas y rendimiento en cada sucursal</p>
                      </div>

                      <div className="store-comparison-grid">
                        {storeList.map(st => {
                          const rendNum = parseFloat(st.rend);
                          const rendClass = rendNum >= 92 ? 'status-excellent' : rendNum >= 88 ? 'status-good' : 'status-warning';
                          return (
                            <div key={st.name} className="store-card glass">
                              <div className="store-card-header">
                                <div>
                                  <h4 className="store-card-title">{st.name}</h4>
                                  <span className="store-card-sessions">{st.count} sesiones de despiece</span>
                                </div>
                                <span className={`store-rend-badge ${rendClass}`}>{st.rend}% Eficiencia</span>
                              </div>

                              <div className="store-metrics-row">
                                <div className="store-metric-item">
                                  <span className="store-metric-lbl">Entrada (Madre)</span>
                                  <span className="store-metric-val">{st.madre.toFixed(1)} KG</span>
                                </div>
                                <div className="store-metric-item">
                                  <span className="store-metric-lbl">Salida (Resultante)</span>
                                  <span className="store-metric-val text-success">{st.res.toFixed(1)} KG</span>
                                </div>
                                <div className="store-metric-item">
                                  <span className="store-metric-lbl">Merma</span>
                                  <span className="store-metric-val text-danger">{st.merma.toFixed(1)} KG</span>
                                </div>
                              </div>

                              <div className="store-bar-meter">
                                <div className="store-bar-fill" style={{ width: `${Math.min(rendNum, 100)}%`, background: rendNum >= 92 ? 'linear-gradient(90deg, #10b981, #059669)' : 'linear-gradient(90deg, #f59e0b, #d97706)' }}></div>
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      {/* SECCIÓN 2: DESGLOSE POR CORTE MADRE */}
                      <div className="transform-section-header" style={{ marginTop: '24px' }}>
                        <h3>🥩 Rendimiento por Tipo de Corte Madre</h3>
                        <p>Desglose de conversión según la pieza de carne ingresada</p>
                      </div>

                      <div className="mother-cuts-grid">
                        {cutList.slice(0, 6).map(cut => (
                          <div key={cut.name} className="mother-cut-card glass">
                            <div className="cut-card-top">
                              <span className="cut-name">{cut.name}</span>
                              <span className="cut-rend-pill">{cut.rend}%</span>
                            </div>
                            <div className="cut-card-details">
                              <span>Ingresado: <strong>{cut.madre.toFixed(1)} KG</strong></span>
                              <span>Obtenido: <strong className="text-success">{cut.res.toFixed(1)} KG</strong></span>
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* SECCIÓN 3: TABLA DETALLADA DE TRANSFORMACIONES */}
                      <div className="report-card glass" style={{ marginTop: '28px' }}>
                        <div className="report-header">
                          <h3>Registros de Transformación y Despiece ({filteredYieldList.length})</h3>
                        </div>

                        {isLoadingYield ? (
                          <div style={{ padding: '60px 0', textAlign: 'center' }}>
                            <div className="spinner-mini" style={{ width: '40px', height: '40px', borderColor: 'rgba(99,102,241,0.2)', borderTopColor: 'var(--primary-color)', margin: '0 auto' }}></div>
                            <p style={{ marginTop: 16, color: 'var(--text-secondary)' }}>Cargando transformaciones...</p>
                          </div>
                        ) : (
                          <div className="report-table-responsive">
                            <table className="report-table">
                              <thead>
                                <tr>
                                  {yieldVisibleCols.Sucursal && <th>Sucursal</th>}
                                  {yieldVisibleCols.FechaHora && <th>Fecha/Hora</th>}
                                  {yieldVisibleCols.Operario && <th>Operario</th>}
                                  {yieldVisibleCols.CorteMadre && <th>Corte Madre (Origen)</th>}
                                  {yieldVisibleCols.PesoMadre && <th className="text-right">Peso Madre (KG)</th>}
                                  {yieldVisibleCols.Lote && <th>Lote</th>}
                                  {yieldVisibleCols.Resultante && <th>Producto Resultante (Destino)</th>}
                                  {yieldVisibleCols.PesoRes && <th className="text-right">Peso Resultante (KG)</th>}
                                  {yieldVisibleCols.RendPct && <th className="text-right">Rendimiento %</th>}
                                  {yieldVisibleCols.MermaKG && <th className="text-right">Merma KG</th>}
                                  {yieldVisibleCols.MermaPct && <th className="text-right">Merma %</th>}
                                </tr>
                              </thead>
                              <tbody>
                                {filteredYieldList.map((r, idx) => {
                                  const rendVal = parseFloat(r['Rendimiento (%)'] || '0');
                                  const rendBadgeClass = rendVal >= 92 ? 'badge-success' : rendVal >= 88 ? 'badge-warning' : 'badge-danger';
                                  return (
                                    <tr key={idx}>
                                      {yieldVisibleCols.Sucursal && <td><span className="store-pill">{r.Sucursal}</span></td>}
                                      {yieldVisibleCols.FechaHora && <td className="text-muted">{r['Fecha/Hora']}</td>}
                                      {yieldVisibleCols.Operario && <td>{r.Operario}</td>}
                                      {yieldVisibleCols.CorteMadre && <td className="font-semibold text-cyan">{r['Corte Madre']}</td>}
                                      {yieldVisibleCols.PesoMadre && <td className="text-right font-bold">{parseFloat(r['Peso Madre (KG)'] || 0).toFixed(2)}</td>}
                                      {yieldVisibleCols.Lote && <td className="text-muted font-mono">{r['Lote Madre']}</td>}
                                      {yieldVisibleCols.Resultante && <td className="font-semibold text-emerald">{r['Producto Resultante']}</td>}
                                      {yieldVisibleCols.PesoRes && <td className="text-right font-bold text-emerald">{parseFloat(r['Peso Resultante (KG)'] || 0).toFixed(2)}</td>}
                                      {yieldVisibleCols.RendPct && <td className="text-right"><span className={`table-rend-pill ${rendBadgeClass}`}>{r['Rendimiento (%)']}</span></td>}
                                      {yieldVisibleCols.MermaKG && <td className="text-right text-rose">{parseFloat(r['Merma Registrada (KG)'] || 0).toFixed(2)}</td>}
                                      {yieldVisibleCols.MermaPct && <td className="text-right text-rose">{r['Merma (%)']}</td>}
                                    </tr>
                                  );
                                })}
                                {filteredYieldList.length === 0 && (
                                  <tr>
                                    <td colSpan="11" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                                      No se encontraron transformaciones con los filtros seleccionados.
                                    </td>
                                  </tr>
                                )}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    </>
                  );
                })()}
              </div>
            )}

            {/* VISTA 4: IMPORTADOR DE EXCEL/CSV DE TANGO */}
            {activeTab === 'importar' && (
              <div className="uploader-card glass fade-in" style={{ maxWidth: '700px' }}>
                <div className="uploader-title-wrapper">
                  <h3>Carga de Movimientos de Tango ERP</h3>
                  <p>Arrastrá o seleccioná el archivo CSV (delimitado por punto y coma) exportado de Tango.</p>
                </div>

                {/* Drag and Drop Zone */}
                <div 
                  className={`drag-zone ${dragActive ? 'drag-active' : ''}`}
                  onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                  onDragLeave={() => setDragActive(false)}
                  onDrop={(e) => {
                    e.preventDefault();
                    setDragActive(false);
                    const file = e.dataTransfer.files[0];
                    if (file) processTangoFile(file);
                  }}
                  onClick={() => document.getElementById('tango-file-input').click()}
                >
                  <div className="upload-icon">📄</div>
                  <p><strong>Elegir archivo</strong> o arrastrarlo aquí</p>
                  <p style={{ fontSize: '0.8rem', marginTop: '4px', color: 'var(--text-secondary)' }}>Formatos compatibles: .csv, .txt (Semicolón ;)</p>
                  <input 
                    id="tango-file-input"
                    type="file"
                    accept=".csv,.txt"
                    onChange={handleTangoFileSelect}
                    style={{ display: 'none' }}
                  />
                </div>

                {/* File Info Preview */}
                {tangoFile && (
                  <div className="fade-in">
                    <div className="file-info-box">
                      <div className="file-details">
                        <div className="file-name">{tangoFile.name}</div>
                        <div className="file-size">{(tangoFile.size / 1024).toFixed(2)} KB — {tangoRows.length} filas detectadas</div>
                      </div>
                      <button 
                        onClick={() => { setTangoFile(null); setTangoRows([]); }} 
                        className="btn-remove-file"
                      >
                        ❌
                      </button>
                    </div>

                    {tangoRows.length > 0 && (
                      <>
                        <div className="preview-title">Vista previa (primeras 3 filas):</div>
                        <div className="report-table-responsive" style={{ maxHeight: 200 }}>
                          <table className="report-table" style={{ fontSize: '0.8rem' }}>
                            <thead>
                              <tr>
                                <th>Fecha</th>
                                <th>Tipo Comp.</th>
                                <th>Artículo</th>
                                <th className="text-right">Cantidad</th>
                                <th>Depósito</th>
                              </tr>
                            </thead>
                            <tbody>
                              {tangoRows.slice(0, 3).map((r, idx) => (
                                <tr key={idx}>
                                  <td>{r['Fecha de Comprobante']}</td>
                                  <td>{r['Tipo comprobante']}</td>
                                  <td>{r['Desc. artículo']}</td>
                                  <td className="text-right font-semibold">{(r['Cantidad control stock'] || 0)}</td>
                                  <td>{r['Depósito']}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </>
                    )}

                    <div className="upload-actions">
                      <button 
                        onClick={handleUploadTangoToSheets}
                        disabled={isUploadingTango || tangoRows.length === 0}
                        className="btn-submit btn-upload-submit"
                      >
                        {isUploadingTango ? (
                          <>
                            <span className="spinner-mini" style={{ marginRight: 8 }}></span>
                            PROCESANDO E IMPORTANDO...
                          </>
                        ) : '📤 IMPORTAR DATOS'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

          </div>
        </div>
      )}

      {/* MODAL / VISOR CÁMARA OCR */}
      {showCamera && (
        <div className="camera-overlay">
          <div className="camera-modal glass">
            <div className="camera-header">
              <h3>
                {cameraState === 'stream' && 'Alinee la etiqueta con el recuadro'}
                {cameraState === 'processing' && 'Procesando lectura...'}
                {cameraState === 'result' && 'Verifique y confirme los datos'}
              </h3>
              <button onClick={stopCamera} className="btn-close-camera">❌</button>
            </div>
            
            <div className="video-container">
              {/* Vista en Vivo */}
              <video 
                ref={videoRef} 
                className="video-preview" 
                playsInline 
                muted
                style={{ display: cameraState === 'stream' ? 'block' : 'none' }}
              ></video>
              
              {/* Cuadrante de guía en vivo */}
              {cameraState === 'stream' && (
                <div className="scanner-target-box">
                  <div className="laser-line"></div>
                </div>
              )}

              {/* Vista Estática Capturada (Congelada) */}
              {cameraState !== 'stream' && capturedImageSrc && (
                <img 
                  src={capturedImageSrc} 
                  alt="Capturado" 
                  className="captured-preview-img" 
                />
              )}

              {/* Spinner de procesamiento */}
              {cameraState === 'processing' && (
                <div className="spinner-overlay">
                  <div className="spinner"></div>
                </div>
              )}
            </div>

            {/* PANEL DE RESULTADOS / ACCIONES */}
            <div className="camera-controls-panel">
              <p className="ocr-status-text-modal">{ocrStatus}</p>

              {/* ESTADO 1: VISTA EN VIVO */}
              {cameraState === 'stream' && (
                <div className="panel-actions-wrapper">
                  <button 
                    onClick={captureFrameAndProcess} 
                    className="btn-camera-action btn-capture"
                  >
                    📸 CAPTURAR Y ANALIZAR
                  </button>
                </div>
              )}

              {/* ESTADO 2: LECTURA COMPLETADA - REVISIÓN Y EDICIÓN */}
              {cameraState === 'result' && (
                <div className="ocr-results-mini-form">
                  {/* Corte OCR */}
                  <div className="mini-form-group relative">
                    <label>Artículo / Corte</label>
                    <input
                      type="text"
                      value={ocrCorteInput}
                      onChange={(e) => {
                        setOcrCorteInput(e.target.value);
                        setOcrCorte(null);
                        setShowOcrCorteDropdown(true);
                      }}
                      onFocus={() => setShowOcrCorteDropdown(true)}
                      placeholder="Seleccione el corte..."
                      className="form-control text-control-mini"
                    />
                    
                    {showOcrCorteDropdown && ocrFilteredCortes.length > 0 && (
                      <div className="predictive-dropdown-mini glass">
                        {ocrFilteredCortes.map(c => (
                          <div
                            key={c.codigo}
                            onClick={() => selectOcrCorte(c)}
                            className="dropdown-item-mini"
                          >
                            <span>{c.descripcion}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Lote OCR */}
                  <div className="mini-form-row">
                    <div className="mini-form-group">
                      <label>Lote</label>
                      <input
                        type="text"
                        value={ocrLote}
                        onChange={(e) => setOcrLote(e.target.value)}
                        placeholder="N° Lote"
                        className="form-control text-control-mini"
                      />
                    </div>

                    {/* Peso OCR */}
                    <div className="mini-form-group">
                      <label>Peso (KG)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={ocrPeso}
                        onChange={(e) => setOcrPeso(e.target.value)}
                        placeholder="Peso KG"
                        className="form-control text-control-mini"
                      />
                    </div>
                  </div>

                  <div className="mini-form-buttons">
                    <button 
                      onClick={retryCapture} 
                      className="btn-camera-action btn-retry"
                    >
                      🔄 VOLVER A INTENTAR
                    </button>
                    <button 
                      onClick={confirmOcrData} 
                      className="btn-camera-action btn-confirm-data"
                    >
                      ✓ AGREGAR A LA SESIÓN
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
          <canvas ref={canvasRef} style={{ display: 'none' }}></canvas>
        </div>
      )}
    </div>
  );
}

export default App;
