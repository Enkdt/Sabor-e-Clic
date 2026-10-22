import './Estoque.css'
import { Banner } from '../Assets/Banner'
import { NextBtn } from '../Components/NextBtn'
import { CardEstoque } from './CardEstoque'
export const Estoque=()=>{
    return (
        <>
            <Banner/>
            <div>
                <h1>Estoque</h1>
                <NextBtn text='Adicionar'/>
                <div>
                    <h1>X produtos no estoque</h1>
                    <CardEstoque/>
                </div>
            </div>
        </>
    )
}