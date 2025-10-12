const API = 'https://entrenaprochile-api.onrender.com'
const out = document.getElementById('output')
document.getElementById('login').addEventListener('click', async ()=>{
  out.textContent = 'Enviando…'
  const email = document.getElementById('email').value
  const password = document.getElementById('password').value
  try{
    const res = await fetch(`${API}/api/usuarios/login`,{
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({email,password})
    })
    const text = await res.text()
    out.textContent = `HTTP ${res.status}\n` + text
  }catch(err){
    out.textContent = 'Error: '+err.message
  }
})
