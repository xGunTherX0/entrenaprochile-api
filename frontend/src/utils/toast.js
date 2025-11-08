// Minimal toast utility: creates a floating message that disappears after a timeout
export default {
  show(message, duration = 2000) {
    try {
      const containerId = 'app-toast-container'
      let container = document.getElementById(containerId)
      if (!container) {
        container = document.createElement('div')
        container.id = containerId
        container.style.position = 'fixed'
        container.style.top = '20px'
        container.style.right = '20px'
        container.style.zIndex = '9999'
        document.body.appendChild(container)
      }

      const el = document.createElement('div')
      el.textContent = message
      el.style.background = 'rgba(0,0,0,0.8)'
      el.style.color = 'white'
      el.style.padding = '10px 14px'
      el.style.marginTop = '8px'
      el.style.borderRadius = '8px'
      el.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)'
      el.style.opacity = '0'
      el.style.transition = 'opacity 160ms ease-in-out, transform 160ms ease'
      el.style.transform = 'translateY(-6px)'

      container.appendChild(el)
      // trigger visible
      requestAnimationFrame(() => {
        el.style.opacity = '1'
        el.style.transform = 'translateY(0)'
      })

      setTimeout(() => {
        el.style.opacity = '0'
        el.style.transform = 'translateY(-6px)'
        setTimeout(() => { try { container.removeChild(el) } catch (e) {} }, 200)
      }, duration)
    } catch (e) {
      // fallback to alert if DOM fails
      try { alert(message) } catch (_) {}
    }
  }
}
