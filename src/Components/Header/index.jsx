import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { PlantIcon, ShoppingCartIcon, UserIcon } from '@phosphor-icons/react'
import { Banner } from '../../Assets/Banner'
import { CartDrawer } from '../CartDrawer'
import './Header.css'
export const Header=()=>{

    const [cartOpen,setCartOpen]=useState(false)

    return(
        <>
            <header className='header'>
                <Banner/>
                <nav className='headerNav px-3 md:px-6 lg:px-10'>
                    <NavLink to='/' className='headerLogo'>
                        {/*Placeholder do logo*/}
                        <PlantIcon className='headerLogoIcon' weight='fill'/>
                        <span className='headerLogoText'>
                            <span>Sabor</span>
                            <span>&</span>
                            <span>Click</span>
                        </span>
                    </NavLink>

                    {/*A barra de pesquisa entra aqui*/}

                    <div className='headerActions gap-4 md:gap-12'>
                        <NavLink to='/login' className='headerAccount'>
                            <UserIcon className='headerIcon'/>
                            <span className='hidden sm:inline'>Acessar Conta</span>
                        </NavLink>
                        <button type='button' aria-label='Abrir carrinho' className='headerCart' onClick={()=>setCartOpen(true)}>
                            <ShoppingCartIcon className='headerIcon'/>
                        </button>
                    </div>
                </nav>
            </header>
            <CartDrawer open={cartOpen} onClose={()=>setCartOpen(false)}/>
        </>
    )
}
