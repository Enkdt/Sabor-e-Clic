import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { House, Moon, PlantIcon, ShoppingCartIcon, Sun, UserIcon, GearIcon, SquaresFourIcon, CookingPotIcon, ForkKnifeIcon, UsersThreeIcon, PackageIcon } from '@phosphor-icons/react'
import { useAuth } from '../../authContext'
import { useTheme } from '../../themeContext'
import { Banner } from '../../Assets/Banner'
import { CartDrawer } from '../CartDrawer'
import { Avatar } from '../Avatar'
import { SkipLink } from '../SkipLink'
import './Header.css'
export const Header=()=>{

    const [cartOpen,setCartOpen]=useState(false)
    const { user } = useAuth()
    const { effective, setPreference } = useTheme()
    const isDark = effective === 'dark'
    const userName = user?.nome?.trim().split(/\s+/)[0] || user?.email?.split('@')[0] || 'usuário'

    // Alterna rapidamente entre claro/escuro; a opção 'sistema' fica em Configurações.
    const toggleTheme = () => setPreference(isDark ? 'light' : 'dark')

    return(
        <>
            <SkipLink/>
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
                                <Avatar src={user.avatar} name={user.nome || user.email} size={26}/>
                                <span>Olá, {userName}!</span>
                            </NavLink>
                            {user.role==='admin' && <NavLink to='/gerente' className='headerHome'>
                                <SquaresFourIcon className='headerIcon'/>
                                <span className='hidden sm:inline'>Gerência</span>
                            </NavLink>}
                            {user.role==='cook' && <NavLink to='/cozinha/minhas-cozinhas' className='headerHome'>
                                <SquaresFourIcon className='headerIcon'/>
                                <span className='hidden sm:inline'>Minhas cozinhas</span>
                            </NavLink>}
                            {user.role==='customer' && <NavLink to='/catalogo/bancadas' className='headerHome'>
                                <ForkKnifeIcon className='headerIcon'/>
                                <span className='hidden sm:inline'>Bancadas</span>
                            </NavLink>}
                            {user.role==='cook' && <NavLink to='/cozinha' className='headerHome'>
                                <CookingPotIcon className='headerIcon'/>
                                <span className='hidden sm:inline'>Cozinha</span>
                            </NavLink>}
                            {user.role==='admin' && <NavLink to='/gerente/staff' className='headerHome'>
                                <UsersThreeIcon className='headerIcon'/>
                                <span className='hidden sm:inline'>Equipe</span>
                            </NavLink>}
                            {user.role==='admin' && <NavLink to='/gerente/estoque' className='headerHome'>
                                <PackageIcon className='headerIcon'/>
                                <span className='hidden sm:inline'>Estoque</span>
                            </NavLink>}
                            {user.role==='cook' && <NavLink to='/cozinha/bancadas' className='headerHome'>
                                <ForkKnifeIcon className='headerIcon'/>
                                <span className='hidden sm:inline'>Bancadas</span>
                            </NavLink>}
                            {user.role==='cook' && <NavLink to='/cozinha/pratos' className='headerHome'>
                                <CookingPotIcon className='headerIcon'/>
                                <span className='hidden sm:inline'>Meus pratos</span>
                            </NavLink>}
                            <NavLink to='/configuracoes' className='headerHome'>
                                <GearIcon className='headerIcon'/>
                                <span className='hidden sm:inline'>Configurações</span>
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
