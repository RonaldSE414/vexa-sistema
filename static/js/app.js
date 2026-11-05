(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const config = window.VEXA_CONFIG || { demo: true, whatsapp: '' };
  const money = (cents) => new Intl.NumberFormat('pt-BR', {style:'currency',currency:'BRL'}).format((cents || 0)/100);
  const escapeHTML = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const storageGet = (key, fallback) => {try{return JSON.parse(localStorage.getItem(key)) ?? fallback}catch{return fallback}};
  const storageSet = (key,value) => {try{localStorage.setItem(key,JSON.stringify(value))}catch{}};
  let products = [];
  let selectedCategory = 'Todos';
  let searchQuery = '';
  let cart = storageGet('vexa_cart', []);
  let toastTimer;

  function toast(text) {
    $('toast').textContent = text;
    $('toast').classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(()=>$('toast').classList.remove('show'), 3200);
  }
  function productCard(p) {
    return `<article class="product-card">
      <div class="product-photo" role="group" aria-label="${escapeHTML(p.nome)}">
        <button class="product-photo" type="button" data-view="${escapeHTML(p.sku)}" aria-label="Ver detalhes de ${escapeHTML(p.nome)}"><img loading="lazy" src="${escapeHTML(p.imagem_url)}" alt="${escapeHTML(p.nome)}"></button>
        ${p.destaque ? '<span class="product-tag">EM DESTAQUE</span>' : ''}
        <button class="quick-add" type="button" data-add="${escapeHTML(p.sku)}" aria-label="Adicionar ${escapeHTML(p.nome)} ao carrinho" title="Adicionar ao carrinho"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M3 4h2l2 11h12l2-8H6"/><circle cx="9" cy="20" r="1"/><circle cx="18" cy="20" r="1"/><path d="M14 7V1m-3 3h6"/></svg></button>
      </div>
      <div class="product-info"><span class="product-category">${escapeHTML(p.categoria)}</span><button class="product-name" type="button" data-view="${escapeHTML(p.sku)}">${escapeHTML(p.nome)}</button><strong class="product-price">${money(p.preco_centavos)}</strong></div>
    </article>`;
  }
  function renderCatalog() {
    let visible = products.filter(p => (selectedCategory === 'Todos' || p.categoria === selectedCategory) && (!searchQuery || (p.nome+' '+(p.descricao||'')).toLocaleLowerCase('pt-BR').includes(searchQuery)));
    $('resultsCount').textContent = `${visible.length} produto${visible.length!==1?'s':''}`;
    $('productGrid').innerHTML = visible.length ? visible.map(productCard).join('') : `<div class="empty-state"><b>Nenhum produto encontrado.</b><span>Tente outra categoria ou busca.</span></div>`;
    document.querySelectorAll('.filter-chip').forEach(b=>b.classList.toggle('active', b.dataset.cat===selectedCategory));
  }
  async function fetchCatalog() {
    try {
      const r = await fetch('/api/products');
      const data = await r.json();
      if (!r.ok) throw new Error(data.erro || 'Não foi possível carregar os produtos.');
      products = data.produtos;
      $('catalogError').hidden = true;
      renderCatalog();
      renderCart();
      await renderRecent();
    } catch (err) {
      $('productGrid').innerHTML = '';
      $('catalogError').hidden = false;
      $('catalogError').textContent = err.message;
    }
  }
  function showCategory(category) {
    selectedCategory = category;
    renderCatalog();
    $('catalogo').scrollIntoView({behavior:'smooth',block:'start'});
  }
  function updateCart() {
    storageSet('vexa_cart',cart);
    $('cartCount').textContent = String(cart.reduce((sum,line)=>sum+line.quantidade,0));
    renderCart();
  }
  function addToCart(sku) {
    const product = products.find(p=>p.sku===sku);
    if (!product) return toast('Produto indisponível.');
    const line = cart.find(x=>x.sku===sku);
    if (line) line.quantidade+=1; else cart.push({sku, quantidade:1});
    updateCart();
    toast('Adicionado ao carrinho ✦');
  }
  function renderCart() {
    const valid = cart.filter(line=>products.some(p=>p.sku===line.sku));
    cart=valid;
    const total = valid.reduce((sum,line)=>sum+(products.find(p=>p.sku===line.sku)?.preco_centavos||0)*line.quantidade,0);
    $('cartTotal').textContent=money(total);
    $('cartCount').textContent=String(valid.reduce((sum,x)=>sum+x.quantidade,0));
    $('checkoutBtn').disabled = !valid.length;
    if(!valid.length){$('cartItems').innerHTML='<div class="drawer-empty"><span>🛒</span><strong>Seu carrinho está vazio.</strong><p>Explore a coleção e encontre algo especial.</p></div>';return;}
    $('cartItems').innerHTML=valid.map(line=>{const p=products.find(p=>p.sku===line.sku);return `<div class="cart-row"><img src="${escapeHTML(p.imagem_url)}" alt="${escapeHTML(p.nome)}"><div class="cart-row-main"><strong>${escapeHTML(p.nome)}</strong><span>${money(p.preco_centavos*line.quantidade)}</span><div class="qty-control"><button type="button" data-qty="${escapeHTML(p.sku)}" data-delta="-1" aria-label="Diminuir quantidade">−</button><b>${line.quantidade}</b><button type="button" data-qty="${escapeHTML(p.sku)}" data-delta="1" aria-label="Aumentar quantidade">+</button><button type="button" class="remove-item" data-remove="${escapeHTML(p.sku)}">Remover</button></div></div></div>`}).join('');
  }
  function updateQuantity(sku,delta) {
    const line=cart.find(x=>x.sku===sku);
    if(!line)return;
    line.quantidade+=delta;
    if(line.quantidade<=0)cart=cart.filter(x=>x.sku!==sku);
    updateCart();
  }
  function showShade(on) { $('screenShade').hidden=!on; document.body.style.overflow=on?'hidden':''; }
  function openCart(){closeModal(false);$('cartDrawer').hidden=false;showShade(true)}
  function closeCart(alsoShade=true){$('cartDrawer').hidden=true;if(alsoShade)showShade(false)}
  function closeModal(alsoShade=true){$('productModal').hidden=true;if(alsoShade)showShade(false)}
  async function openProduct(sku) {
    try {
      const r=await fetch('/api/products/'+encodeURIComponent(sku));
      const data=await r.json();
      if(!r.ok)throw new Error(data.erro||'Não foi possível abrir o produto.');
      const p=data.produto;
      if(config.demo){let ids=storageGet('vexa_recent_demo',[]).filter(id=>id!==sku);ids.unshift(sku);storageSet('vexa_recent_demo',ids.slice(0,6));}
      closeCart(false);
      $('modalContent').innerHTML=`<div class="modal-layout"><div class="modal-photo"><img src="${escapeHTML(p.imagem_url)}" alt="${escapeHTML(p.nome)}"></div><div class="modal-copy"><span class="product-category">${escapeHTML(p.categoria)} / VEXA</span><h2>${escapeHTML(p.nome)}</h2><p>${escapeHTML(p.descricao||'Uma escolha especial para você.')}</p><strong class="product-price">${money(p.preco_centavos)}</strong><button type="button" class="btn btn-primary" data-add="${escapeHTML(p.sku)}">Adicionar ao carrinho <span>↗</span></button></div></div>`;
      $('productModal').hidden=false;
      showShade(true);
      renderRecent();
    } catch(err){toast(err.message)}
  }
  async function renderRecent(){
    try{
      let recent=[];
      if(config.demo){const ids=storageGet('vexa_recent_demo',[]);recent=ids.map(id=>products.find(p=>p.sku===id)).filter(Boolean);$('recentExplainer').textContent='Prévia: histórico armazenado neste navegador. No modo integrado, o histórico será lido do Redis.';}
      else{const r=await fetch('/api/recent');const d=await r.json();if(!r.ok)throw new Error(d.erro);recent=d.produtos;}
      $('recentSection').hidden=recent.length===0;
      $('recentGrid').innerHTML=recent.map(p=>`<button type="button" class="recent-item" data-view="${escapeHTML(p.sku)}"><img src="${escapeHTML(p.imagem_url)}" alt="${escapeHTML(p.nome)}"><span>${escapeHTML(p.nome)}</span></button>`).join('');
    }catch(err){$('recentSection').hidden=true;toast(err.message)}
  }
  async function checkout(){
    if (!cart.length) return;
    if (!config.whatsapp) { toast('Configure o WhatsApp da loja no arquivo .env.'); return; }
    // Abre na interação com o botão para evitar bloqueadores de pop-up.
    const popup = window.open('', '_blank');
    if (popup) popup.opener = null;
    $('checkoutBtn').disabled = true;
    try {
      const response = await fetch('/api/checkout', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({itens: cart})
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.erro || 'Não foi possível preparar o pedido.');
      if (popup) popup.location.replace(body.url);
      else window.location.href = body.url;
    } catch(error) {
      if (popup) popup.close();
      toast(error.message);
    } finally { $('checkoutBtn').disabled = cart.length === 0; }
  }
  document.addEventListener('click',(e)=>{
    const add=e.target.closest('[data-add]');if(add){addToCart(add.dataset.add);return;}
    const view=e.target.closest('[data-view]');if(view){openProduct(view.dataset.view);return;}
    const filter=e.target.closest('[data-cat]');if(filter){showCategory(filter.dataset.cat);return;}
    const qty=e.target.closest('[data-qty]');if(qty){updateQuantity(qty.dataset.qty,Number(qty.dataset.delta));return;}
    const remove=e.target.closest('[data-remove]');if(remove){cart=cart.filter(x=>x.sku!==remove.dataset.remove);updateCart();}
  });
  $('searchInput').addEventListener('input',e=>{searchQuery=e.target.value.trim().toLocaleLowerCase('pt-BR');renderCatalog()});
  $('goSearch').addEventListener('click',()=>{$('catalogo').scrollIntoView({behavior:'smooth'});setTimeout(()=>$('searchInput').focus(),400)});
  $('cartOpen').addEventListener('click',openCart);
  $('cartClose').addEventListener('click',closeCart);
  $('screenShade').addEventListener('click',()=>{closeCart();closeModal()});
  $('modalClose').addEventListener('click',closeModal);
  $('checkoutBtn').addEventListener('click',checkout);
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeCart();closeModal()}});
  fetchCatalog();
})();
