import './Carrinho.css'
import { Banner } from '../Assets/Banner'
import { CardCarrinho } from './CardCarrinho'
import { NotaCarrinho } from './NotaCarrinho'
export const Carrinho=()=>{
    return (
        <>
            <Banner />
            <div>
                <h1>Meu Carrinho</h1> <br />
                <div>
                    <CardCarrinho /> <br />
                </div>
                <div>
                    <NotaCarrinho />
                </div>
            </div>
        </>
    )
}