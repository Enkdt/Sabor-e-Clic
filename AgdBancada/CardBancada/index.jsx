import './CardBancada.css'
import { CardBancadaImg } from '../../Assets/CardBancadaImg/CardBancadaImg'
export const CardBancada=()=>{
    return(
        <div>
            <CardBancadaImg/> 
            <div>
                <button>
                    Detalhes
                </button>
                <br />
                <button>
                    Agendar Bancada
                </button>
            </div>
        </div>
    )
}