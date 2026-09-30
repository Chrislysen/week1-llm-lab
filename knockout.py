"""knockout.py: greedy decoding with attention knockout for Hugging Face causal LMs.

A knockout forbids a set of query positions from attending to a set of key positions, in
chosen layers (all heads), during the prompt's forward pass. Optionally the generated tokens
are also forbidden from a set of prompt keys. Everything else attends normally.

The model always receives an explicit 4D additive mask (transformers returns a 4D mask as-is,
masking_utils._preprocess_mask_arguments). In the chosen layers a forward pre-hook on the
attention module swaps in the knocked-out mask.

    text, n = greedy(model, tok, ids, blocks=[(queries, keys)], layers=range(0, 14))
"""
import torch


def knockout_mask(n, blocks, dtype, device="cpu"):
    """(1, 1, n, n) additive mask: causal, plus each (queries, keys) pair blocked."""
    neg = torch.finfo(dtype).min
    m = torch.full((n, n), neg, dtype=dtype, device=device).triu(1)
    for q, k in blocks:
        qi = torch.as_tensor(sorted(q), dtype=torch.long, device=device)
        ki = torch.as_tensor(sorted(k), dtype=torch.long, device=device)
        assert len(qi) and len(ki), "empty knockout span"
        assert int(ki.min()) < int(qi.max()), "keys after every query: nothing to block"
        m[qi.unsqueeze(1), ki.unsqueeze(0)] = neg
    assert (m.diagonal() == 0).all(), "a token must always see itself"
    return m[None, None]


def _attention_modules(model):
    return [layer.self_attn for layer in model.model.layers]


@torch.no_grad()
def greedy(model, tok, ids, blocks=(), new_keys=(), layers=None, max_new_tokens=512, stop_ids=None):
    """Greedy continuation of `ids` (1, n).

    blocks    [(queries, keys)] blocked in the prompt's forward pass, in `layers`
    new_keys  prompt positions the generated tokens may not attend to, in `layers`
    layers    layer indexes the knockout applies to (default: all)
    """
    stop = set(stop_ids or [tok.eos_token_id])
    n, dtype, dev = ids.shape[1], model.dtype, ids.device
    neg = torch.finfo(dtype).min
    plain = knockout_mask(n, [], dtype, dev)
    ko = knockout_mask(n, blocks, dtype, dev) if blocks else plain
    new_keys = sorted(new_keys)
    mods = _attention_modules(model)
    chosen = range(len(mods)) if layers is None else layers

    def hook(module, args, kwargs):
        m = kwargs["attention_mask"]
        if m.shape[-2] > 1:
            kwargs["attention_mask"] = ko
        elif new_keys:
            m = m.clone()
            m[..., new_keys] = neg
            kwargs["attention_mask"] = m
        return args, kwargs

    handles = [mods[i].register_forward_pre_hook(hook, with_kwargs=True) for i in chosen] \
        if (blocks or new_keys) else []
    try:
        out = model(input_ids=ids, attention_mask=plain, use_cache=True)
        past, new = out.past_key_values, []
        nxt = out.logits[0, -1].argmax()
        for _ in range(max_new_tokens):
            t = int(nxt)
            if t in stop:
                break
            new.append(t)
            step = torch.tensor([[t]], device=dev)
            zero = torch.zeros((1, 1, 1, n + len(new)), dtype=dtype, device=dev)
            out = model(input_ids=step, attention_mask=zero, past_key_values=past, use_cache=True)
            past = out.past_key_values
            nxt = out.logits[0, -1].argmax()
    finally:
        for h in handles:
            h.remove()
    return tok.decode(new, skip_special_tokens=True), len(new)


def char_span_to_tokens(offsets, start, end):
    """Token indexes whose character span overlaps [start, end)."""
    return [i for i, (a, b) in enumerate(offsets) if b > a and a < end and b > start]
