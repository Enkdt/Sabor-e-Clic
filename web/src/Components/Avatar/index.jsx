import { initials, colorFor } from '../../utils/avatarColor'
import './Avatar.css'

// Avatar com fallback: mostra a imagem quando houver; caso contrário, iniciais
// sobre uma cor determinística derivada do nome (default sem precisar gerar imagem).
export const Avatar=({ src, name, size=48, shape='round', className='' })=>{
    const dim={ width:size, height:size, fontSize:Math.round(size*0.4) }
    const radius=shape==='round' ? '50%' : '8px'
    if(src){
        return (
            <span className={`avatar ${className}`} style={{ ...dim, borderRadius:radius }}>
                <img src={src} alt={name ? `Foto de ${name}` : 'Foto'} style={{ borderRadius:radius }}/>
            </span>
        )
    }
    return (
        <span
            className={`avatar avatarFallback ${className}`}
            style={{ ...dim, borderRadius:radius, backgroundColor:colorFor(name) }}
            role='img'
            aria-label={name ? `Foto de ${name}` : 'Sem foto'}
        >
            {initials(name)}
        </span>
    )
}
