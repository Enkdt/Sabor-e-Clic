import './CardBancada.css'
import { CardBancadaImg } from '../../Assets/CardBancadaImg/CardBancadaImg'
import { NavLink } from 'react-router-dom'
export const CardBancada=({ bancada })=>{
    const endereco=bancada.endereco
    return(
        <article className='cardBancada'>
            <div className='cardBancadaThumb'><CardBancadaImg/></div>
            <div className='cardBancadaInfo'>
                <h2>{bancada.nome}</h2>
                {endereco && <p className='cardBancadaAddress'>{endereco.rua}, {endereco.numero} — {endereco.bairro}, {endereco.cidade}</p>}
            </div>
            <div className='cardBancadaActions'>
                <NavLink to={`/bancada/${bancada.id}`} className='cardBancadaDetails'>Detalhes</NavLink>
                <NavLink to={`/bancada/${bancada.id}`} className='cardBancadaBook'>Agendar Bancada</NavLink>
            </div>
        </article>
    )
}
