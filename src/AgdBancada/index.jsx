import { Banner } from '../Assets/Banner'
import { CardBancada } from './CardBancada'
import './AgdBancada.css'
export const AgdBancada=()=>{
    return (
        <>
            <Banner/>
            <div>
                <h1>Agende uma Bancada</h1>
            </div>
            <div>
                Agende com a Sabor&Click uma bancada com todos os itens necessários para tornar suas receitas ainda mais deliciosas
            </div>

            <div>
                <h1>Horários e datas disponíveis</h1>
            </div>

            <CardBancada/>
        </>
    )
}