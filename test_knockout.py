"""Zero-data checks of the knockout machinery on a tiny random Llama (CPU, no downloads)."""
import torch
from transformers import LlamaConfig, LlamaForCausalLM

from knockout import char_span_to_tokens, greedy, knockout_mask

N_LAYERS = 4


def tiny():
    torch.manual_seed(0)
    cfg = LlamaConfig(vocab_size=97, hidden_size=64, intermediate_size=128, num_hidden_layers=N_LAYERS,
                      num_attention_heads=4, num_key_value_heads=2, max_position_embeddings=256)
    return LlamaForCausalLM(cfg).eval().to(torch.float32)


class Tok:
    eos_token_id = 0

    def decode(self, ids, skip_special_tokens=True):
        return " ".join(map(str, ids))


def recompute(m, ids, steps, masks_for):
    """Reference: recompute the whole sequence each step with explicit per-layer masks."""
    seq = ids
    for _ in range(steps):
        L = seq.shape[1]
        per_layer = masks_for(L)
        handles = []
        for i, layer in enumerate(m.model.layers):
            def hook(mod, args, kwargs, mk=per_layer[i]):
                kwargs["attention_mask"] = mk
                return args, kwargs
            handles.append(layer.self_attn.register_forward_pre_hook(hook, with_kwargs=True))
        try:
            nxt = m(input_ids=seq, attention_mask=knockout_mask(L, [], torch.float32)).logits[0, -1].argmax()
        finally:
            for h in handles:
                h.remove()
        seq = torch.cat([seq, nxt.view(1, 1)], dim=1)
    return " ".join(map(str, seq[0, ids.shape[1]:].tolist()))


def test_a_plain_causal_mask_changes_nothing():
    m = tiny()
    ids = torch.randint(1, 97, (1, 40))
    ref = m(input_ids=ids).logits
    got = m(input_ids=ids, attention_mask=knockout_mask(40, [], torch.float32)).logits
    assert torch.allclose(ref, got, atol=1e-5)
    assert greedy(m, Tok(), ids, max_new_tokens=6, stop_ids=[-1])[0] == \
        recompute(m, ids, 6, lambda L: [knockout_mask(L, [], torch.float32)] * N_LAYERS)


def test_a_knockout_changes_only_later_positions():
    m = tiny()
    ids = torch.randint(1, 97, (1, 40))
    ref = m(input_ids=ids).logits
    got = m(input_ids=ids, attention_mask=knockout_mask(40, [(range(20, 25), range(5, 10))], torch.float32)).logits
    assert torch.allclose(ref[0, :20], got[0, :20], atol=1e-5)
    assert not torch.allclose(ref[0, 20:], got[0, 20:], atol=1e-3)


def test_cached_decoding_equals_recompute_for_prompt_blocks_in_chosen_layers():
    m = tiny()
    ids = torch.randint(1, 97, (1, 30))
    blocks, layers = [(range(20, 25), range(5, 10))], [0, 2]
    got = greedy(m, Tok(), ids, blocks=blocks, layers=layers, max_new_tokens=8, stop_ids=[-1])[0]
    want = recompute(m, ids, 8, lambda L: [knockout_mask(L, blocks if i in layers else [], torch.float32)
                                           for i in range(N_LAYERS)])
    assert got == want, (got, want)


def test_cached_decoding_equals_recompute_when_new_tokens_are_blocked_too():
    m = tiny()
    ids = torch.randint(1, 97, (1, 30))
    keys = range(10, 14)

    def masks(L):
        after = range(14, L)
        return [knockout_mask(L, [(after, keys)], torch.float32)] * N_LAYERS

    got = greedy(m, Tok(), ids, blocks=[(range(14, 30), keys)], new_keys=keys, max_new_tokens=8, stop_ids=[-1])[0]
    assert got == recompute(m, ids, 8, masks)


def test_the_knockout_changes_the_continuation_on_this_toy():
    m = tiny()
    ids = torch.randint(1, 97, (1, 30))
    keys = range(0, 29)
    base = greedy(m, Tok(), ids, max_new_tokens=8, stop_ids=[-1])[0]
    ko = greedy(m, Tok(), ids, blocks=[(range(29, 30), keys)], new_keys=keys, max_new_tokens=8, stop_ids=[-1])[0]
    assert base != ko


def test_char_spans_map_to_overlapping_tokens():
    offsets = [(0, 0), (0, 3), (3, 4), (4, 9), (9, 10), (10, 15)]
    assert char_span_to_tokens(offsets, 3, 9) == [2, 3]
    assert char_span_to_tokens(offsets, 4, 12) == [3, 4, 5]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
