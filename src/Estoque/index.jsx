import './Estoque.css'
import { Banner } from '../Assets/Banner'
import { NextBtn } from '../Components/NextBtn'
import { NavLink } from 'react-router-dom'
import { CardEstoque } from './CardEstoque'
export const Estoque=()=>{
    return (
        <>
            <Banner/>
            <div>
                <h1>Estoque</h1>
                <NavLink to='/AdcEstoque'>
                    <NextBtn text='Adicionar'/>
                </NavLink>
                <div>
                    <h1>X produtos no estoque</h1>
                    <CardEstoque/>
                </div>
            </div>
        </>
    )
}