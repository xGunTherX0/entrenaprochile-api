<template>
  <div class="min-h-screen text-white bg-gray-900">
    <!-- Hero -->
    <section class="relative">
      <div class="container-max py-12">
        <div class="relative h-[60vh] md:h-[72vh] rounded-xl overflow-hidden surface-card shadow-2xl" :style="heroStyle">
          <div class="absolute inset-0 bg-black/45"></div>
          <div class="relative h-full px-6 py-20 flex items-center">
            <div class="max-w-2xl text-white">
              <h1 class="text-4xl md:text-5xl font-extrabold leading-tight mb-4">Bienvenido a EntrenaProChile</h1>
              <p class="text-lg md:text-xl text-gray-200/85 mb-8">La mejor plataforma para entrenadores y deportistas. Conecta, crea rutinas y monetiza tu trabajo.</p>
              <div class="flex items-center gap-4">
                <router-link to="/login" class="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-cyan-400 to-green-400 text-black font-semibold rounded-full shadow focus-ring">Iniciar sesión</router-link>
                <router-link to="/register" class="inline-flex items-center gap-2 px-5 py-3 border border-white/10 text-white rounded-full hover:bg-white/5">Regístrate</router-link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features / Benefits section -->
    <main class="max-w-6xl mx-auto px-6 py-16 space-y-12">
      <section>
        <h2 class="text-3xl md:text-4xl font-extrabold text-white mb-3">Beneficios Clave para Entrenadores</h2>
        <p class="text-gray-300 max-w-3xl mb-8">Nuestra plataforma está diseñada para apoyar tu éxito, ofreciendo una amplia gama de herramientas para ayudarte a gestionar clientes, crear programas de entrenamiento efectivos y hacer crecer tu negocio.</p>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div v-for="(f, i) in features" :key="i"
               @click="activeIndex = i"
               role="button"
               tabindex="0"
               @keydown.enter.prevent="activeIndex = i"
               :class="[
                 'p-6 rounded-2xl transition-transform transition-shadow cursor-pointer transform-gpu',
                 activeIndex === i
                   ? 'scale-105 bg-gradient-to-br from-indigo-700 to-blue-500 text-white shadow-2xl ring-4 ring-indigo-400/20 border-transparent'
                   : 'bg-gray-900/20 border border-gray-800 hover:scale-[1.02] hover:shadow-lg'
               ]">
            <div class="flex items-center gap-3 mb-4">
              <div :class="[
                  activeIndex === i ? 'w-12 h-12 rounded-lg bg-white/10 text-white text-lg' : 'w-10 h-10 rounded-md bg-blue-600/20 text-blue-400 text-base',
                  'flex items-center justify-center'
                ]">{{ f.icon }}</div>
              <h3 :class="['font-semibold', activeIndex === i ? 'text-white' : 'text-white']">{{ f.title }}</h3>
            </div>
            <p :class="['text-sm', activeIndex === i ? 'text-white/90' : 'text-gray-300']">{{ f.short }}</p>
          </div>
        </div>
      </section>

      <!-- Lower dynamic feature row with image (changes according to selected top card) -->
      <section class="grid grid-cols-1 lg:grid-cols-12 items-center gap-8">
        <div class="lg:col-span-4">
          <div class="p-6 rounded-2xl bg-gray-900/30 border border-gray-800 mb-6">
            <div class="flex items-start gap-4">
              <div class="w-10 h-10 rounded-full bg-blue-600/20 flex items-center justify-center">{{ current.left.icon }}</div>
              <div>
                <h4 class="font-semibold text-white">{{ current.left.title }}</h4>
                <p class="text-gray-300 text-sm">{{ current.left.desc }}</p>
              </div>
            </div>
          </div>

          <div class="p-6 rounded-2xl bg-gray-900/30 border border-gray-800">
            <div class="flex items-start gap-4">
              <div class="w-10 h-10 rounded-full bg-blue-600/20 flex items-center justify-center">{{ current.left2.icon }}</div>
              <div>
                <h4 class="font-semibold text-white">{{ current.left2.title }}</h4>
                <p class="text-gray-300 text-sm">{{ current.left2.desc }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="lg:col-span-4 flex items-center justify-center">
          <div class="w-full max-w-md rounded-3xl overflow-hidden bg-gray-800/20 shadow-lg">
            <div class="h-72 bg-cover bg-center" :style="`background-image: url('${current.image}')`"></div>
          </div>
        </div>

        <div class="lg:col-span-4">
          <div class="p-6 rounded-2xl bg-gray-900/30 border border-gray-800 mb-6">
            <div class="flex items-start gap-4">
              <div class="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center">{{ current.right.icon }}</div>
              <div>
                <h4 class="font-semibold text-white">{{ current.right.title }}</h4>
                <p class="text-gray-300 text-sm">{{ current.right.desc }}</p>
              </div>
            </div>
          </div>

          <div class="p-6 rounded-2xl bg-gray-900/30 border border-gray-800">
            <div class="flex items-start gap-4">
              <div class="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">{{ current.right2.icon }}</div>
              <div>
                <h4 class="font-semibold text-white">{{ current.right2.title }}</h4>
                <p class="text-gray-300 text-sm">{{ current.right2.desc }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script>
export default {
  name: 'Home',
  data() {
    return {
      activeIndex: 0,
      features: [
        {
          title: 'Gestión de Clientes',
          short: 'Administra todos tus clientes en un solo lugar con fácil acceso a sus perfiles, planes de entrenamiento y datos de progreso.',
          icon: '👥',
          image: '/hero.png',
          left: { icon: '✓', title: 'Administra todos tus clientes', desc: 'Consulta rápidamente el historial, evaluaciones y metas de cada cliente desde un solo panel de control.' },
          left2: { icon: '📋', title: 'Perfiles personalizados', desc: 'Crea perfiles detallados con sus métricas físicas, objetivos, notas y planes asignados.' },
          right: { icon: '🔔', title: 'Visor de clientes activos', desc: 'Gestiona tus clientes activos e inactivos.' },
          right2: { icon: '⚙️', title: 'Control de progresión', desc: 'Ajusta pesos, repeticiones y descansos conforme el cliente progresa.' }
        },
        {
          title: 'Gestión de Rutinas',
          short: 'Crea rutinas de entrenamiento personalizadas con un instructor amigable.',
          icon: '🏋️',
          image: '/hero.png',
          left: { icon: '📅', title: 'Planificación estructurada', desc: 'Diseña rutinas semanales con días específicos, ejercicios personalizados y recomendaciones.' },
          left2: { icon: '🏛️', title: 'Biblioteca de ejercicios', desc: 'Accede a cientos de ejercicios categorizados por grupo muscular y nivel de dificultad.' },
          right: { icon: '📊', title: 'Comparaciones visuales', desc: 'Visualiza gráficas de progreso físico (peso, grasa, masa muscular) por fecha.' },
          right2: { icon: '📝', title: 'Evaluaciones completas', desc: 'Registra evaluaciones periódicas con fotos, medidas y notas de rendimiento.' }
        },
        {
          title: 'Gestión de plan nutricional',
          short: 'Facilitamos el registro de un plan nutricional para cada deportista que lo necesite.',
          icon: '🥗',
          image: '/hero.png',
          left: { icon: '🥗', title: 'Nutrición adaptada', desc: 'Asigna planes alimenticios con calorías y macros según el objetivo del cliente.' },
          left2: { icon: '📄', title: 'Exportación PDF', desc: 'Genera y comparte el plan nutricional con tus clientes de forma profesional.' },
          right: { icon: '🎯', title: 'Seguimiento de metas', desc: 'Asigna metas por cliente y mide el avance con indicadores visuales.' },
          right2: { icon: '📈', title: 'Comparaciones visuales', desc: 'Visualiza gráficos de progreso por periodos específicos.' }
        },
        {
          title: 'Seguimiento del Progreso',
          short: 'Rastrea el progreso de los deportistas con registros detallados de entrenamientos y análisis de rendimiento.',
          icon: '📈',
          image: '/hero.png',
          left: { icon: '📊', title: 'Comparaciones visuales', desc: 'Visualiza gráficas de progreso físico (peso, grasa, masa muscular) por fecha.' },
          left2: { icon: '🧾', title: 'Evaluaciones completas', desc: 'Registra evaluaciones periódicas con fotos, medidas y notas de rendimiento.' },
          right: { icon: '🎯', title: 'Seguimiento de metas', desc: 'Asigna metas por cliente y mide el avance con indicadores visuales.' },
          right2: { icon: '⚙️', title: 'Control de progresión', desc: 'Ajusta pesos, repeticiones y descansos conforme el cliente progresa.' }
        }
      ]
    }
  },
  computed: {
    heroStyle() {
      return `background-image: url('/hero_top.jpg'); background-size: cover; background-position: center;`;
    },
    current() {
      return this.features[this.activeIndex] || this.features[0]
    }
  }
}
</script>
