import { useState } from 'react';
import { LoginImg } from '../../Assets/LoginImg';
import { SignBtn } from '../../Assets/SignBtn';
import { NextBtn } from '../../Components/NextBtn';
import { LoginDivider } from '../LoginDivider';
import { Input } from '../../Components/Input';
import './LoginForm.css';
import { NavLink, useNavigate } from 'react-router-dom';
export const LoginForm=()=>{

    const navigate=useNavigate();
    const [email,setEmail] = useState('');
    const [password,setPassword] = useState('');
    const [error,setError]=useState('');

    const cleanForm=()=>{
        
    }

    const loginLogic = async (e) => {
        e.preventDefault();

        const response = await fetch('/api/login',{
            //Metodo post ou get
            method: 'POST', 
            //Especificação do tipo de dado
            headers: {'Content-Type':'application/json'},
            //O que vai ser enviado
            body: JSON.stringify({email: email, password:password})
        })
        //Vai só enviar, a validation vai ser no python

        const data = await response.json();
        console.log(data);
        if(!response.ok){
            //caso algum erro tenha ocorrido, como senha/email errados ou invalidos
            setError(data.error.message);
            return;
        }
        //Redireciona para a home page caso o login esteja bem sucedido :o
        if(response.ok){
            navigate("/");
        }
        //limpar inputs depois de submeter o login
    }

    const inputs=[
        {
            label:"E-mail",
            placeholder:"exemplo@email.com",
            type:"text",
            value: email,
            onChange: (e) => setEmail(e.target.value)
        },
        {
            label:"Senha",
            placeholder:"Insira a sua senha",
            type:"password",
            //Pra botar os valores como tiver do input
            value: password,
            onChange: (e) => setPassword(e.target.value)
        }
    ]

return (
    <div className="loginDiv">
        <LoginImg/>

        <div className="loginForm w-full max-w-[800px]">
            <form onSubmit={loginLogic}>
                <h1 className="loginTitle transition-all duration-500 ease text-[44px] md:text-[54px] lg:text-[64px]">Bem-Vindo de volta!</h1>

                {inputs.map((input) => (
                    <div key={input.label}>
                        <Input
                            label={input.label}
                            placeholder={input.placeholder}
                            type={input.type}
                            value={input.value}
                            onChange={input.onChange}
                            className={error ? "loginInput error" : "loginInput"}
                        />

                        <p style={{ opacity: error ? 1 : 0 }} className="loginError">
                            {error || "errorPlaceholder"}
                        </p>
                    </div>
                ))}
                <NextBtn text="Continuar"/>
            </form>

            <LoginDivider/>
            <NavLink to="/cadastro">
                <SignBtn text="Cadastrar-se"/>
            </NavLink>
        </div>
    </div>
);

}