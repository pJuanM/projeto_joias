// Declaraar função que será chamada quando o usuário clicar em um pedido (recebendo o id deste pedido)
function verDetalhesPedido(id){
    // Faz uma requisição GET para o endpoint do Flask /pedido/<id> usando o valor recebido.
    fetch(`/pedidos/${id}`)
    // Transforma a resposta do servidor (que é JSON) em um objeto JavaScript.
    .then(res => res.json())
    // Começa a trabalhar com os dados recebidos da API.
    .then(data => {
        // Se a resposta tiver um erro (como "Pedido não encontrado"), mostra um alerta e encerra a função.
        if (data.erro) {
            alert(data.erro);
            return;
        }
        
        // Dados do cliente
        // Insere dinamicamente o nome, telefone e CPF do cliente dentro do elemento .info_cliente_text.
        document.querySelector(".info_cliente_text").innerHTML = `
            <p>${data.cliente.nome}</p>
            <p>${data.cliente.telefone}</p>
            <p>${data.cliente.cpf}</p>
        `;
        
        // Número do pedido
        // Mostra o número do pedido no cabeçalho da seção do pedido.
        document.querySelector(".info_num_ped").textContent = `Pedido #${data.id}`;

        // Data do pedido
        // Converte a data do pedido para formato brasileiro (ex: 18/06/2025) e atualiza o campo de data.
        const dataFormatada = new Date(data.data_pedido).toLocaleDateString("pt-BR");
        document.querySelector(".info_pedido_time").textContent = `Data: ${dataFormatada}`;

        // Tabela de itens
        // Seleciona o tbody da tabela e limpa o conteúdo anterior (caso tenha sido exibido outro pedido antes).
        const corpoTabela = document.querySelector(".info_pedido-itens tbody");
        corpoTabela.innerHTML = ""; // Limpa a tabela anterior
        //Percorre cada item do pedido e cria uma linha da tabela com os dados:
        // Nome do item
        // Cor do pano
        // Valor unitário (formatado com duas casas decimais)
        // Quantidade
        // Total
        // Cada linha é injetada dentro da tabela.
        data.itens.forEach(item => {
            const linha = `
            <tr>
                <td>${item.nome}</td>
                <td>${item.cor_pano}</td>
                <td>R$ ${item.valor_unitario.toFixed(2)}</td>
                <td>${item.quantidade}</td>
                <td>R$ ${item.total.toFixed(2)}</td>
            </tr>
            `;
            corpoTabela.innerHTML += linha;
        });
        // Mostrar overlay
        // Mostra o elemento com o ID overlay, que provavelmente cobre a tela com o card de informações.
        document.getElementById("overlay").style.display = "block";
    });
}

function verDetalhesCliente(id) {
    fetch(`/clientes/${id}`)
    .then(res => res.json())
    .then(data => {
        if (data.erro) {
            alert(data.erro);
            return;
        }
        const clientes_tabela =  document.querySelector(".info_cliente_text");
        clientes_tabela.innerHTML = "";
        clientes_tabela.innerHTML = `
            <p><strong>Nome: </strong> </p>
            <p>${data.nome}</p>
            <p><strong>Telefone:</strong> </p>
            <p>${data.telefone}</p>
            <p><strong>CPF: </strong></p>
            <p>${data.cpf}</p>
        `;
        document.getElementById("overlay").style.display = "block";
    });   
}
function verDetalhesPagamento(id) {
    fetch(`/pagamentos/${id}`)
    .then(res => res.json())
    .then(data => {
        if (data.erro) {
            alert(data.erro);
            return;
        }
        const pagamentos_tabela = document.querySelector(".info_pagamento_text");
        pagamentos_tabela.innerHTML = "";
        pagamentos_tabela.innerHTML = `
            <p><strong>Pedido:</strong></p>
            <p>${data.pedido}</p>
            <p><strong>Valor Pago:</strong></p>
            <p>${data.valor_pago}</p>
            <p><strong>Data Pagamento: </strong></p>
            <p>${data.data_pagamento}</p>
        `;
        document.getElementById("overlay").style.display = "block";
    });
}

// Botão de fechar
// Quando o botão "Fechar" é clicado, oculta o card de detalhes
document.getElementById("fechar_info_extras").addEventListener("click", () => {
  document.getElementById("overlay").style.display = "none";
});


