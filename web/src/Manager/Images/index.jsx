import { useEffect, useState } from 'react'
import { Header } from '../../Components/Header'
import { ImageUploader } from '../../Components/ImageUploader'
import { setRestaurantImage, setDishImage, createRestaurant } from '../../authSession'
import './Images.css'

export const Images=()=>{
    const [restaurants,setRestaurants]=useState([])
    const [status,setStatus]=useState('loading') // loading | ready | error
    const [selected,setSelected]=useState(null) // restaurante carregado com pratos
    const [novoNome,setNovoNome]=useState('')
    const [criando,setCriando]=useState(false)
    const [erro,setErro]=useState('')

    const carregar=()=>{
        fetch('/api/restaurantes')
            .then(async (r)=>{ const d=await r.json(); if(!r.ok) throw new Error(); return d.restaurantes })
            .then((list)=>{ setRestaurants(list); setStatus('ready') })
            .catch(()=>setStatus('error'))
    }

    useEffect(()=>{ carregar() },[])

    const criar=async (e)=>{
        e.preventDefault()
        if(criando || !novoNome.trim()) return
        setCriando(true); setErro('')
        try{
            await createRestaurant(novoNome.trim())
            setNovoNome('')
            carregar()
        }catch(err){ setErro(err.message) }
        finally{ setCriando(false) }
    }

    const abrir=async (id)=>{
        setSelected({ id, loading:true })
        try{
            const r=await fetch(`/api/restaurantes/${id}`)
            const d=await r.json()
            if(!r.ok) throw new Error()
            setSelected(d.restaurante)
        }catch{
            setSelected({ id, erro:true })
        }
    }

    return(
        <main id='conteudo-principal' className='imagesPage'>
            <Header/>
            <div className='imagesContent'>
                <h1>Restaurantes</h1>
                <form className='imagesCreate' onSubmit={criar}>
                    <input
                        value={novoNome}
                        onChange={(e)=>setNovoNome(e.target.value)}
                        placeholder='Nome do novo restaurante'
                        maxLength={30}
                        aria-label='Nome do novo restaurante'
                    />
                    <button type='submit' disabled={criando}>{criando ? 'Criando…' : 'Criar restaurante'}</button>
                </form>
                {erro && <p role='alert' className='imagesError'>{erro}</p>}
                {status==='loading' && <p role='status'>Carregando restaurantes…</p>}
                {status==='error' && <p role='alert'>Não foi possível carregar os restaurantes.</p>}
                {status==='ready' && (
                    <div className='imagesGrid'>
                        {restaurants.map((rest)=>(
                            <section key={rest.id} className='imagesCard'>
                                <h2>{rest.nome}</h2>
                                <ImageUploader
                                    current={rest.imagem}
                                    label='foto'
                                    shape='square'
                                    onUpload={(key)=>setRestaurantImage(rest.id,key).catch(()=>{})}
                                />
                                <button type='button' className='imagesDishesToggle' onClick={()=>abrir(rest.id)}>
                                    {selected?.id===rest.id ? 'Recarregar pratos' : 'Gerenciar pratos'}
                                </button>
                                {selected?.id===rest.id && selected.loading && <p role='status'>Carregando pratos…</p>}
                                {selected?.id===rest.id && selected.erro && <p role='alert'>Falha ao carregar pratos.</p>}
                                {selected?.id===rest.id && selected.pratos && (
                                    <ul className='imagesDishes'>
                                        {selected.pratos.map((prato)=>(
                                            <li key={prato.id}>
                                                <span>{prato.nome}</span>
                                                <ImageUploader
                                                    current={prato.imagem}
                                                    label='foto'
                                                    shape='square'
                                                    onUpload={(key)=>setDishImage(prato.id,key).catch(()=>{})}
                                                />
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </section>
                        ))}
                    </div>
                )}
            </div>
        </main>
    )
}
