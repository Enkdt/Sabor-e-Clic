import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { CaretDownIcon } from '@phosphor-icons/react'
import { createIngredient, updateIngredient, fetchIngredients } from '../../authSession'
import { Header } from '../../Components/Header'
import { Input } from '../../Components/Input'
import { NextBtn } from '../../Components/NextBtn'
import { ImageUploader } from '../../Components/ImageUploader'
import './StockAdd.css'

const UNIDADES=['kg','g','L','mL','un']

export const StockAdd=()=>{

    const navigate=useNavigate()
    const { id }=useParams()
    const isEdit=Boolean(id)

    const [nome,setNome]=useState('')
    const [validade,setValidade]=useState('')
    const [quantidade,setQuantidade]=useState('')
    const [unidade,setUnidade]=useState('')
    const [imagem,setImagem]=useState(null) // chave do upload
    const [imagemUrl,setImagemUrl]=useState(null)
    const [status,setStatus]=useState(isEdit ? 'loading' : 'idle') // idle | loading | saving | error
    const [errors,setErrors]=useState({})
    const [message,setMessage]=useState('')

    // Em modo edição, carrega o item atual (reusa a listagem; o volume de estoque é pequeno).
    useEffect(()=>{
        if(!isEdit) return
        let active=true
        fetchIngredients()
            .then((list)=>{
                const item=list.find((i)=>String(i.id)===String(id))
                if(!active) return
                if(!item){ setStatus('error'); setMessage('Item não encontrado.'); return }
                setNome(item.nome)
                setValidade(item.validade)
                setQuantidade(String(item.quantidade))
                setUnidade(item.unidade)
                setImagemUrl(item.imagem || null)
                setStatus('idle')
            })
            .catch(()=>{ if(active){ setStatus('error'); setMessage('Não foi possível carregar o item.') } })
        return ()=>{ active=false }
    },[id,isEdit])

    const submit=async (e)=>{
        e.preventDefault()
        if(status==='saving') return
        setStatus('saving')
        setErrors({})
        setMessage('')
        const payload={ nome, validade, quantidade: Number(quantidade), unidade }
        if(imagem) payload.imagem=imagem // só envia se trocou a imagem nesta sessão
        try{
            if(isEdit){ await updateIngredient(id,payload) }
            else{ await createIngredient(payload) }
            navigate('/gerente/estoque')
        }catch(error){
            setStatus('error')
            setErrors(error.fields || {})
            setMessage(error.fields ? 'Corrija os campos destacados.' : error.message)
        }
    }

    if(status==='loading'){
        return <main id='conteudo-principal' className='stockAddPage'><Header/><p role='status' className='px-4 py-8'>Carregando item…</p></main>
    }

    return(
        <main id='conteudo-principal' className='stockAddPage'>
            <Header/>
            <div className='stockAddForm px-4 py-8 md:px-10 lg:px-[88px]'>
                <h1 className='text-[28px] md:text-[36px]'>{isEdit ? 'Editar item do estoque' : 'Adição de itens ao estoque'}</h1>
                <form onSubmit={submit}>
                    <Input label='Nome Produto' placeholder='Insira o nome do produto' type='text' value={nome} onChange={(e)=>setNome(e.target.value)} className='loginInput'/>
                    {errors.nome && <p role='alert' className='stockAddError'>{errors.nome}</p>}

                    <Input label='Data de validade' placeholder='AAAA-MM-DD' type='date' value={validade} onChange={(e)=>setValidade(e.target.value)} className='loginInput'/>
                    {errors.validade && <p role='alert' className='stockAddError'>{errors.validade}</p>}

                    <Input label='Quantidade' placeholder='Insira a quantidade do produto' type='number' value={quantidade} onChange={(e)=>setQuantidade(e.target.value)} className='loginInput'/>
                    {errors.quantidade && <p role='alert' className='stockAddError'>{errors.quantidade}</p>}

                    <div className='stockAddSelects grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-[40px]'>
                        <div className='stockAddField'>
                            <label htmlFor='stock-unidade'>Unidade de medida</label>
                            <div className='stockAddSelect'>
                                <select id='stock-unidade' value={unidade} onChange={(e)=>setUnidade(e.target.value)}>
                                    <option value='' disabled>Selecione a unidade de medida</option>
                                    {UNIDADES.map((option)=>(
                                        <option key={option} value={option}>{option}</option>
                                    ))}
                                </select>
                                <CaretDownIcon className='stockAddSelectIcon'/>
                            </div>
                            {errors.unidade && <p role='alert' className='stockAddError'>{errors.unidade}</p>}
                        </div>
                    </div>

                    {message && <p role='alert' className='stockAddError'>{message}</p>}

                    <div className='stockAddField'>
                        <label>Foto do produto</label>
                        <ImageUploader current={imagemUrl} label='foto' shape='square' onUpload={(key,url)=>{ setImagem(key); setImagemUrl(url) }}/>
                    </div>

                    <NextBtn text={status==='saving' ? 'Salvando…' : (isEdit ? 'Salvar' : 'Adicionar')}/>
                </form>
            </div>
        </main>
    )
}
