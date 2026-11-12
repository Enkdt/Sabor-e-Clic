import { useEffect, useRef } from 'react'
import './ConfirmDialog.css'

// Diálogo de confirmação acessível para ações destrutivas.
// Uso controlado: renderize com open=true e passe onConfirm/onCancel.
export const ConfirmDialog=({
    open,
    title='Confirmar ação',
    message,
    confirmLabel='Confirmar',
    cancelLabel='Cancelar',
    danger=true,
    busy=false,
    onConfirm,
    onCancel,
})=>{
    const confirmRef=useRef(null)

    useEffect(()=>{
        if(!open) return
        // Foca o botão de confirmar ao abrir e fecha com Esc.
        confirmRef.current?.focus()
        const onKey=(e)=>{ if(e.key==='Escape' && !busy) onCancel?.() }
        document.addEventListener('keydown',onKey)
        return ()=>document.removeEventListener('keydown',onKey)
    },[open,busy,onCancel])

    if(!open) return null

    return(
        <div className='confirmDialogOverlay' onClick={()=>{ if(!busy) onCancel?.() }}>
            <div
                className='confirmDialog'
                role='alertdialog'
                aria-modal='true'
                aria-labelledby='confirmDialogTitle'
                aria-describedby={message ? 'confirmDialogMsg' : undefined}
                onClick={(e)=>e.stopPropagation()}
            >
                <h2 id='confirmDialogTitle' className='confirmDialogTitle'>{title}</h2>
                {message && <p id='confirmDialogMsg' className='confirmDialogMsg'>{message}</p>}
                <div className='confirmDialogActions'>
                    <button type='button' className='confirmDialogCancel' onClick={()=>onCancel?.()} disabled={busy}>
                        {cancelLabel}
                    </button>
                    <button
                        type='button'
                        ref={confirmRef}
                        className={danger ? 'confirmDialogConfirm confirmDialogConfirm--danger' : 'confirmDialogConfirm'}
                        onClick={()=>onConfirm?.()}
                        disabled={busy}
                    >
                        {busy ? 'Processando…' : confirmLabel}
                    </button>
                </div>
            </div>
        </div>
    )
}
