import './CardBancada.css'
import { CardBancadaImg } from '../../Assets/CardBancadaImg/CardBancadaImg'
import { NavLink } from 'react-router-dom'
import { NextBtn } from '../../Components/NextBtn'
export const CardBancada=({ bancada })=>{
    return(
        <div>
            <CardBancadaImg/> 
            <div>
                <h2>{bancada.nome}</h2>
                {bancada.endereco && <p>{bancada.endereco.rua}, {bancada.endereco.numero} — {bancada.endereco.bairro}, {bancada.endereco.cidade}</p>}
                <NavLink to={`/Bancada/${bancada.id}`}>
                    <NextBtn text='Agendar Bancada'/>
                </NavLink>
            </div>
        </div>
    )
}
