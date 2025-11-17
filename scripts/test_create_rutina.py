from backend import auth
import requests

token = auth.generate_token({'user_id':7,'role':'entrenador','nombre':'Test'})
print('TOKEN:', token)
url='http://127.0.0.1:5000/api/rutinas'
payload={
 'nombre':'test from assistant',
 'descripcion':'desc',
 'objetivo_principal':'obj',
 'enfoque_rutina':'enc',
 'cualidades_clave':'cual',
 'duracion_frecuencia':'dur',
 'material_requerido':'mat',
 'instrucciones_estructurales':'inst',
 'nivel':'Básico',
 'entrenador_id':'7'
}
headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'}
try:
 r=requests.post(url,json=payload,headers=headers,timeout=10)
 print('STATUS',r.status_code)
 try:
     print('BODY',r.json())
 except Exception:
     print('BODY RAW',r.text[:1000])
except Exception as e:
 print('REQUEST ERROR',e)
