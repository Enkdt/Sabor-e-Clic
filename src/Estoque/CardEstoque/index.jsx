import './CardEstoque.css'
import { CardEstoqueImg } from '../../Assets/CardEstoqueImg'
import { NextBtn } from '../../Components/NextBtn'
import { NavLink } from 'react-router-dom'
export const CardEstoque=()=>{
    return (
        <>
            <CardEstoqueImg/>
            <h1>Arroz Integral</h1> 
            Cereal <br /> 
            <br />
            Quantidade <br />
            Data Adição <br />
            Data Validade <br />

            <NavLink>
                <NextBtn text='Editar'/>
            </NavLink>
        </>
    )
}