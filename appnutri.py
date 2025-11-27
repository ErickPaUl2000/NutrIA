#Importar librerias
import streamlit as st
from google import genai
import os
from datetime import datetime

#Configuración de la página de Streamlit
st.set_page_config(
    page_title="NutrIA 🥗",
    layout='wide',
    initial_sidebar_state='expanded'
)

st.title('NutrIA 🦦 : Tu Asesor Nutricional con IA')
st.markdown("Usa la IA para generar planes de comidas, analizar recetas y obtener consejos dietéticos personalizados.")
st.divider()

#Configuración de la IA

#1. Cargar la clave API de forma segura
try:
    # Intenta cargar la clave desde secrets.toml (método recomendado en Streamlit)
    api_key = st.secrets["gemini_api_key"]
except (FileNotFoundError, KeyError):
    # Si falla, intenta cargarla desde las variables de entorno (para pruebas locales rápidas)
    api_key = os.environ.get("GEMINI_API_KEY")
    st.error("Error: Clave API de Gemini no encontrada. Asegúrate de configurarla en `.streamlit/secrets.toml` o como variable de entorno.")
    st.stop()

cliente = genai.Client(api_key=api_key)
MODEL_NAME = 'gemini-2.5-flash'

#Intrucciones del Sistema: Define el rol de la IA
SYSTEM_INSTRUCTION = (
    "Eres un dietista y nutricionista experto. Tu misión es proporcionar "
    "información precisa, balanceada y basada en evidencia sobre dietas, "
    "planes de comidas y valor nutricional. **Formatea tu respuesta usando Markdown "
    "(encabezados, listas y negritas) para que sea fácil de leer.** "
    "Sé profesional y alienta siempre hábitos saludables."
)

#Función para llamar a la IA

def gen_cont_nutri(prompt_usuario):
    '''
    Llama al modelo de Gemini con la instrucción del sistema y el prompt del usuario.
    '''
    try: 
        with st.spinner("🧠 La IA está generando tu plan..."):
            response = cliente.models.generate_content(
                model = MODEL_NAME,
                contents = prompt_usuario,
                config = genai.types.GenerateContentConfig(
                    system_instruction = SYSTEM_INSTRUCTION
                )
            )
        return response.text
    except Exception as e:
        return f'Ocurrio un error al contactar a la IA: {e}'

#Interfaz de Streamlit

#sidebar para los parámetros del usuario
st.sidebar.header('Mis Parámetros')

#Campos de entrada
objetivo = st.sidebar.text_input(
    "1. Objetivo Nutricional"
    )

#Datos antropométricos (Edad, Talla, Peso)
edad = st.sidebar.text_input(
    "2. Edad (años)"
    )
talla = st.sidebar.number_input(
    "3. Talla (cm)",
    min_value=50, max_value=300, value=170, step=1
)
peso = st.sidebar.number_input(
    "4. Peso (kg)",
    min_value=1.0, max_value=500.0, value=70.0, step=0.1, format="%.1f"
)

contexto_adicional = st.sidebar.text_area(
    "4. Contexto (ej. Diagnostico del paciente)",
    height=100
    )

#Formulación del Prompt

#Cración del prompt que le enviaremos a la IA
prompt_final = (
    f"Por favor, actúa como mi asesor nutricional y genera un tratamiento nutricional, distribución de la molécula calórica y el diagnóstico nutrición basado en la terminología de nutrición"
    f"basado en la siguiente información:\n\n"
    f"- **Objetivo Principal:** {objetivo}\n"
    f"- **Edad:** {edad} años\n"
    f"- **Talla:** {talla} cm\n"
    f"- **Peso:** {peso} kg\n"
    f"- **Contexto Adicional:** {contexto_adicional}\n\n"
   )

#Zona de consulta libre

st.header('Consulta rapida nutricional')
pregunta_libre = st.text_area(
    "Hazle una pregunta directa al nutricionista IA: ",
    height=100
)

if st.button('Obtener Respuesta'):
    if pregunta_libre:
        resultado_libre = gen_cont_nutri(pregunta_libre)
        st.markdown('---')
        st.subheader('Respuesta del Nutricionista IA: ')
        st.info(resultado_libre)
    else:
        st.warning('Por favor, escribe una pregunta para la consulta libre.')

# Inicializar st.session_state si no existen (necesario para el primer run)
if 'prompt_usado' not in st.session_state:
    st.session_state['prompt_usado'] = ''
if 'mostrar_boton_guardar' not in st.session_state:
    st.session_state['mostrar_boton_guardar'] = False
if 'resultado_ia' not in st.session_state:
    st.session_state['resultado_ia'] = ''
if 'objetivo_actual' not in st.session_state:
    st.session_state['objetivo_actual'] = ''

#Mostrar Prompt
#if st.session_state.get('prompt_usado'):
    #with st.expander('Ver prompt enviado a la IA (solo desarrollador)'):
        #st.code(st.session_state['prompt_usado'], language = 'markdown')

#Directorio para guardar planes
saved_plans_dir = 'planes_nutricionales_guardados'
if not os.path.exists(saved_plans_dir):
    os.makedirs(saved_plans_dir)

def guardar_plan_generado(plan_texto, objetivo):
    """
    Guarda el texto del plan nutricional en un archivo con un nombre único.
    """
    # Genera un nombre de archivo único con fecha, hora y el objetivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Limpia el objetivo para usarlo en el nombre del archivo
    # Usar un hash simple si el objetivo es muy largo o contiene caracteres especiales complejos
    import re
    nombre_limpio = re.sub(r'\W+', '_', objetivo).lower()[:30] # Limita a 30 caracteres
    if not nombre_limpio: # Si el objetivo era solo caracteres especiales
        nombre_limpio = 'plan_personalizado'
    
    filename = f"{timestamp}_{nombre_limpio}.txt"
    filepath = os.path.join(saved_plans_dir, filename)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(plan_texto)
        return True, filename
    except Exception as e:
        return False, str(e)
        
#  FUNCIÓN PARA DESCARGAR
def crear_boton_descarga(filepath, filename):
    """
    Crea y muestra un botón de descarga para un archivo específico.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            contenido = f.read()
        
        st.download_button(
            label="Descargar Plan (TXT)",
            data=contenido,
            file_name=filename,
            mime="text/plain"
        )
    except Exception as e:
        st.error(f"Error al preparar la descarga del archivo: {e}")
        
#Boton de generar
if st.sidebar.button('General Plan Nutricional', type = 'primary'):
    if not (objetivo and edad and talla and peso):
        st.error('Por favor, rellena todos los campos')
    else:
        resultado_ia = gen_cont_nutri(prompt_final)

        #guardar el resultado para mostrarlo en el área principal
        st.session_state['resultado_ia'] = resultado_ia
        st.session_state['prompt_usado'] = prompt_final
        st.session_state['objetivo_actual'] = objetivo

        #plan generado
        st.subheader('Plan generado con éxito')
        st.markdown(resultado_ia)

        #plan guardado
        st.session_state['mostrar_boton_guardar'] = True
        
# ⬅️ Botón de Guardar se muestra fuera del if principal para persistir después del rerun
if st.session_state.get('mostrar_boton_guardar') and st.session_state.get('resultado_ia'):
    if st.button("💾 Guardar este Plan"):
        exito, resultado = guardar_plan_generado(st.session_state['resultado_ia'], st.session_state['objetivo_actual'])
        if exito:
            st.success(f"Plan guardado exitosamente como **{resultado}** en la carpeta **{saved_plans_dir}**.")
            st.session_state['mostrar_boton_guardar'] = False # Ocultar tras guardar
        else:
            st.error(f"Error al guardar el plan: {resultado}")

st.divider()
      
# --- Sección de Historial de Planes ---
st.header("📚 Historial de Planes Guardados")

# Obtener todos los archivos .txt de la carpeta
try:
    archivos_guardados = [f for f in os.listdir(saved_plans_dir) if f.endswith('.txt')]
    archivos_guardados.sort(reverse=True) # Mostrar el más reciente primero
except FileNotFoundError:
    st.warning(f"La carpeta '{saved_plans_dir}' aún no existe o está vacía.")
    archivos_guardados = []
except Exception as e:
     # Manejo de otros posibles errores de OS
    st.error(f"Error al leer la carpeta de planes: {e}")
    archivos_guardados = []

if archivos_guardados:
    plan_seleccionado = st.selectbox(
        "Selecciona un plan guardado para ver su contenido:",
        archivos_guardados
    )
    
    if plan_seleccionado:
        filepath = os.path.join(saved_plans_dir, plan_seleccionado)

        # Botón para mostrar el contenido
        if st.button(f"Abrir: {plan_seleccionado}"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    contenido_plan = f.read()
                
                st.subheader(f"Contenido de: {plan_seleccionado}")
                st.markdown(contenido_plan)
            except Exception as e:
                st.error(f"Error al leer el archivo: {e}")
                
        #OPCIÓN DE DESCARGA
        st.markdown("---")
        st.subheader("Descargar Plan Nutricional")
        # Llama a la nueva función para mostrar el botón de descarga
        crear_boton_descarga(filepath, plan_seleccionado) 
        
else:
    st.info("Aún no tienes planes guardados. ¡Genera uno y guárdalo!")











