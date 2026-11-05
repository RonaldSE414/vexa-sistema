(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const conf = window.VEXA_ADMIN || {preview:true,csrf:''};
  const money = cents => new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format((cents||0)/100);
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let products=[];
  let editing=null;
  let timer;
  function toast(message){$('toast').textContent=message;$('toast').classList.add('show');clearTimeout(timer);timer=setTimeout(()=>$('toast').classList.remove('show'),3200)}
  async function load(){
    try{
      const r=await fetch('/api/products');const d=await r.json();if(!r.ok)throw Error(d.erro||'Erro ao carregar catálogo');
      products=d.produtos;
      $('adminTotal').textContent=products.length;
      $('adminCategories').textContent=new Set(products.map(p=>p.categoria)).size;
      $('adminStatus').textContent=conf.preview?'Prévia':'Ativo';
      $('adminStatusDesc').textContent=conf.preview?'Dados de demonstração':'MongoDB conectado';
      render();
    }catch(err){$('adminRows').innerHTML=`<tr><td colspan="5">${esc(err.message)}</td></tr>`;$('adminStatus').textContent='Offline';$('adminStatusDesc').textContent='Verifique o MongoDB'}
  }
  function render(){
    const q=$('adminSearch').value.toLocaleLowerCase('pt-BR');
    const shown=products.filter(p=>p.nome.toLocaleLowerCase('pt-BR').includes(q)||p.categoria.toLocaleLowerCase('pt-BR').includes(q));
    $('adminRows').innerHTML=shown.length?shown.map(p=>`<tr><td><div class="table-product"><img src="${esc(p.imagem_url)}" alt=""><span>${esc(p.nome)}<br><small style="color:#9aadba">${esc(p.sku)}</small></span></div></td><td>${esc(p.categoria)}</td><td><strong>${money(p.preco_centavos)}</strong></td><td><span class="status-pill">No catálogo</span></td><td><button type="button" class="action-btn" data-edit="${esc(p.sku)}">Editar</button><button type="button" class="action-btn danger" data-delete="${esc(p.sku)}">Excluir</button></td></tr>`).join(''):'<tr><td colspan="5">Nenhum produto encontrado.</td></tr>';
  }
  function closeForm(){ $('productFormOverlay').hidden=true;document.body.style.overflow=''; }
  function openForm(sku){
    editing=sku||null;
    $('productForm').reset();
    const p=products.find(p=>p.sku===sku);
    $('formTitle').textContent=p?'Editar produto':'Novo produto';
    $('skuField').readOnly=!!p;
    if(p){
      for(const name of ['nome','categoria','descricao','sku']){$('productForm').elements[name].value=p[name]||''}
      $('productForm').elements.preco.value=(p.preco_centavos/100).toFixed(2);
      $('productForm').elements.destaque.checked=!!p.destaque;
    }
    $('productFormOverlay').hidden=false;
    document.body.style.overflow='hidden';
  }
  async function save(e){
    e.preventDefault();
    if(conf.preview){toast('Essa é apenas a prévia. Configure o MongoDB e faça login para salvar.');return;}
    const data=new FormData($('productForm'));
    data.set('destaque',$('productForm').elements.destaque.checked?'true':'false');
    const path=editing?'/api/admin/products/'+encodeURIComponent(editing):'/api/admin/products';
    $('formSubmit').disabled=true;
    try{
      const r=await fetch(path,{method:editing?'PUT':'POST',headers:{'X-CSRF-Token':conf.csrf},body:data});
      const d=await r.json();if(!r.ok)throw Error(d.erro||'Falha ao salvar');
      toast(editing?'Produto atualizado no MongoDB.':'Produto cadastrado no MongoDB.');
      closeForm();await load();
    }catch(err){toast(err.message)}finally{$('formSubmit').disabled=false}
  }
  async function remove(sku){
    if(conf.preview){toast('Prévia: exclusão desabilitada.');return;}
    const p=products.find(p=>p.sku===sku);
    if(!window.confirm('Excluir '+(p?.nome||sku)+' do catálogo?'))return;
    try{const r=await fetch('/api/admin/products/'+encodeURIComponent(sku),{method:'DELETE',headers:{'X-CSRF-Token':conf.csrf}});const d=await r.json();if(!r.ok)throw Error(d.erro||'Não foi possível excluir');toast('Produto removido do MongoDB.');await load()}
    catch(err){toast(err.message)}
  }
  $('addProductBtn').addEventListener('click',()=>openForm());
  $('formClose').addEventListener('click',closeForm);
  $('formCancel').addEventListener('click',closeForm);
  $('productFormOverlay').addEventListener('click',e=>{if(e.target===$('productFormOverlay'))closeForm()});
  $('productForm').addEventListener('submit',save);
  $('adminSearch').addEventListener('input',render);
  $('adminRows').addEventListener('click',e=>{const edit=e.target.closest('[data-edit]');const del=e.target.closest('[data-delete]');if(edit)openForm(edit.dataset.edit);if(del)remove(del.dataset.delete)});
  document.addEventListener('keydown',e=>{if(e.key==='Escape')closeForm()});
  if($('logoutBtn'))$('logoutBtn').addEventListener('click',async()=>{try{const r=await fetch('/admin/logout',{method:'POST',headers:{'X-CSRF-Token':conf.csrf}});if(r.ok)location.href='/admin/login';else toast('Falha ao sair')}catch{toast('Falha de conexão')}});
  load();
})();
