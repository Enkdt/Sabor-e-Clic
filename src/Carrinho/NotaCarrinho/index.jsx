import './NotaCarrinho.css'
import { NextBtn } from '../../Components/NextBtn'
import { NavLink } from 'react-router-dom'
export const NotaCarrinho=()=>{
    return (
        <>
            <h1>Endereço</h1>
            Rua Augusta - 120 - República <br />
            <br />
            Subtotal
            Descontos
            <h1>Total do Pedido</h1>
            <NavLink to='/'>
                <NextBtn text='Continuar'/>
            </NavLink>
        </>
    )
}