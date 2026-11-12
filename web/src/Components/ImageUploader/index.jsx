import { useRef, useState } from 'react'
import { uploadImage } from '../../authSession'
import './ImageUploader.css'

// Fluxo com confirmação: escolher arquivo → pré-visualizar → Confirmar/Cancelar.
// Só chama onUpload(key, url) após o Confirmar, evitando trocas acidentais.
export const ImageUploader=({ current, onUpload, label='Imagem', shape='square' })=>{
    const [saved,setSaved]=useState(current || null)   // imagem já persistida
    const [pending,setPending]=useState(null)           // { url, key } aguardando confirmação
    const [status,setStatus]=useState('idle')           // idle | uploading | confirming | error
    const [error,setError]=useState('')
    const inputRef=useRef(null)

    const escolher=async (e)=>{
        const file=e.target.files?.[0]
        if(!file) return
        setStatus('uploading'); setError('')
        try{
            const { key, url }=await uploadImage(file)
            setPending({ key, url })
            setStatus('confirming')
        }catch(err){
            setStatus('error')
            setError(err.message)
        }finally{
            if(inputRef.current) inputRef.current.value='' // permite reescolher o mesmo arquivo
        }
    }

    const confirmar=()=>{
        if(!pending) return
        setSaved(pending.url)
        onUpload(pending.key, pending.url)
        setPending(null)
        setStatus('idle')
    }

    const cancelar=()=>{
        setPending(null)
        setStatus('idle')
        setError('')
    }

    const mostrada=pending?.url || saved
    const confirming=status==='confirming'

    return(
        <div className='imageUploader'>
            <div className={`imageUploaderPreview imageUploaderPreview--${shape} ${confirming ? 'isPending' : ''}`}>
                {mostrada
                    ? <img src={mostrada} alt={label}/>
                    : <span className='imageUploaderEmpty'>Sem imagem</span>}
            </div>

            {confirming
                ? <div className='imageUploaderConfirm'>
                    <p className='imageUploaderHint' role='status'>Pré-visualização — confirme para salvar.</p>
                    <div className='imageUploaderActions'>
                        <button type='button' className='imageUploaderSave' onClick={confirmar}>Confirmar</button>
                        <button type='button' className='imageUploaderCancel' onClick={cancelar}>Cancelar</button>
                    </div>
                  </div>
                : <label className='imageUploaderButton'>
                    {status==='uploading' ? 'Enviando…' : `Trocar ${label.toLowerCase()}`}
                    <input ref={inputRef} type='file' accept='image/png,image/jpeg,image/webp' onChange={escolher} disabled={status==='uploading'}/>
                  </label>}

            {status==='error' && <p role='alert' className='imageUploaderError'>{error}</p>}
        </div>
    )
}
