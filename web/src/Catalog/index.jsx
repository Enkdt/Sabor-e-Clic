import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { Header } from '../Components/Header'
import { RestaurantCard } from '../Home/RestaurantCard'
import './Catalog.css'

export const Catalog=()=>{
    const [restaurants,setRestaurants]=useState([])
    const [status,setStatus]=useState('loading')

    useEffect(()=>{
        let active=true
        fetch('/api/restaurantes')
            .then(async (response)=>{
                const data=await response.json()
                if(!response.ok) throw new Error(data.error?.message || 'Falha ao carregar restaurantes.')
                return data.restaurantes
            })
            .then((items)=>{ if(active){ setRestaurants(items); setStatus('ready') } })
            .catch(()=>{ if(active) setStatus('error') })
        return ()=>{ active=false }
    },[])

    return(
        <main id='conteudo-principal' className='catalogPage'>
            <Header/>
            <div className='catalogContent max-w-[1390px] mx-auto'>
                <h1 className='catalogTitle'>Todos os restaurantes</h1>
                {status==='loading' && <p>Carregando restaurantes…</p>}
                {status==='error' && <p role='alert'>Não foi possível carregar os restaurantes.</p>}
                {status==='ready' && restaurants.length===0 && <p>Nenhum restaurante disponível no momento.</p>}
                {status==='ready' && restaurants.length>0 && <div className='catalogGrid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 justify-items-center gap-x-[56px] gap-y-[32px] w-full mx-auto'>
                    {restaurants.map((restaurant)=>(
                        <NavLink key={restaurant.id} to={`/restaurante/${restaurant.slug || restaurant.id}`} className='block w-full'>
                            <RestaurantCard id={restaurant.id} restaurantName={restaurant.nome} tag1={restaurant.categorias[0] || ''} tag2={restaurant.categorias[1] || ''} image={restaurant.imagem}/>
                        </NavLink>
                    ))}
                </div>}
            </div>
        </main>
    )
}
