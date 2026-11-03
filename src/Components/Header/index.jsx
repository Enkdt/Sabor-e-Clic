import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { House, Moon, PlantIcon, ShoppingCartIcon, Sun, UserIcon } from '@phosphor-icons/react'
import { useAuth } from '../../authContext'
import { Banner } from '../../Assets/Banner'
import { CartDrawer } from '../CartDrawer'
import './Header.css'
export const Header=()=>{

    const [cartOpen,setCartOpen]=useState(false)
    const { user } = useAuth()
    const [isDark, setIsDark] = useState(() => {
        const preference = localStorage.getItem('theme-preference') || 'system'
        return preference === 'dark' || (preference === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
    })
    const userName = user?.nome?.trim().split(/\s+/)[0] || user?.email?.split('@')[0] || 'usuário'

    const toggleTheme = () => {
        const nextIsDark = !isDark
        setIsDark(nextIsDark)
        localStorage.setItem('theme-preference', nextIsDark ? 'dark' : 'light')
        document.documentElement.dataset.theme = nextIsDark ? 'dark' : 'light'
        document.documentElement.style.colorScheme = nextIsDark ? 'dark' : 'light'
    }

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

                    <div className='headerActions gap-2 sm:gap-4 md:gap-8'>
                        {user ? <>
                            <NavLink to='/perfil' className='headerGreeting'>
                                <UserIcon className='headerIcon'/>
                                <span>Olá, {userName}!</span>
                            </NavLink>
                            <NavLink to='/' className='headerHome'>
                                <House className='headerIcon'/>
                                <span className='hidden sm:inline'>Início</span>
                            </NavLink>
                        </> : <NavLink to='/login' className='headerAccount'>
                            <UserIcon className='headerIcon'/>
                            <span className='hidden sm:inline'>Acessar Conta</span>
                        </NavLink>}
                        <button
                            type='button'
                            aria-label={isDark ? 'Ativar tema claro' : 'Ativar tema escuro'}
                            title={isDark ? 'Ativar tema claro' : 'Ativar tema escuro'}
                            className='headerTheme'
                            onClick={toggleTheme}
                        >
                            {isDark ? <Moon className='headerIcon' weight='fill'/> : <Sun className='headerIcon' weight='fill'/>}
                        </button>
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
