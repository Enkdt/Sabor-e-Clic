import './CardBancada.css'
import { CardBancadaImg } from '../../Assets/CardBancadaImg/CardBancadaImg'
import { NavLink } from 'react-router-dom'
import { NextBtn } from '../../Components/NextBtn'
export const CardBancada=()=>{
    return(
        <div>
            <CardBancadaImg/> 
            <div>
                <button>
                    Detalhes
                </button>
                <br />
                <NavLink to='/Bancada'>
                    <NextBtn text='Agendar Bancada'/>
                </NavLink>
            </div>
        </div>
    )
}