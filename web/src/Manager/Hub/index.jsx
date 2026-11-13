import { NavLink } from 'react-router-dom'
import { Header } from '../../Components/Header'
import './Hub.css'

const LINKS=[
    { to:'/gerente/dashboard', titulo:'Dashboard', descricao:'Métricas de vendas e pedidos.' },
    { to:'/gerente/restaurantes/metricas', titulo:'Métricas por restaurante', descricao:'Desempenho detalhado de cada restaurante.' },
    { to:'/gerente/estoque', titulo:'Estoque', descricao:'Ingredientes e quantidades.' },
    { to:'/gerente/staff', titulo:'Equipe', descricao:'Criar contas de cozinha e administração.' },
    { to:'/gerente/filiacoes', titulo:'Filiações', descricao:'Vincular cozinheiros a restaurantes.' },
    { to:'/gerente/imagens', titulo:'Restaurantes', descricao:'Criar restaurantes e gerenciar fotos de restaurantes e pratos.' },
]

export const Hub=()=>{
    return(
        <main id='conteudo-principal' className='hubPage'>
            <Header/>
            <div className='hubContent'>
                <h1>Gerência</h1>
                <ul className='hubGrid'>
                    {LINKS.map((link)=>(
                        <li key={link.to}>
                            <NavLink to={link.to} className='hubCard'>
                                <span className='hubCardTitle'>{link.titulo}</span>
                                <span className='hubCardDesc'>{link.descricao}</span>
                            </NavLink>
                        </li>
                    ))}
                </ul>
            </div>
        </main>
    )
}
