# พรอมท์เจนคลิปปักตะกร้า: Google Flow vs Meta AI

> รวบรวม 12 ต.ค. 2026 ต่อจาก `research-ai-clip-prompts-shopee-affiliate.md`
> **ข้อจำกัด:** พรอมท์ "สำเร็จรูป" ที่คนไทยแจก (เช่น Lemon8 @kingpirate91, @nattawut.puphet) อยู่ในคอมเมนต์/ลิงก์ Facebook ซึ่งเปิดจากเครื่องที่ใช้ค้นไม่ได้ (นโยบายเครือข่ายบล็อก)
> เลยแยกเป็น 2 ส่วน: **(ก) พรอมท์/แพทเทิร์นที่ดึงมาได้จริงจากแหล่ง** และ **(ข) พรอมท์พร้อมใช้ที่ผมเขียนจากแพทเทิร์นเหล่านั้น**

---

## สรุปคำแนะนำ (TL;DR)

| อันดับ | เครื่องมือ | แบบคลิป | ทำไม |
|---|---|---|---|
| 🥇 1 | **Google Flow** | **F1 ตัวละครคนเดิมรีวิว + ถือสินค้า (Ingredients)** | สินค้าตรงของจริงที่สุด (สำคัญเพราะ Shopee ห้ามสินค้าเพี้ยนจากของจริง), พูดไทยลิปซิงก์ได้, มีฮุก-เดโม-CTA ครบ → ขายได้จริง |
| 🥈 2 | **Google Flow** | **F2 หมี Bear Friends ขายของ** | ตรงแบรนด์ช่อง, คนจำได้, การ์ตูนไม่ต้องกังวลเรื่องปลอมหน้าคนจริง, เด่นในฟีดที่คลิป UGC AI ล้น |
| 🥉 3 | **Google Flow** | **F3 ก่อน/หลัง (Frames to Video)** | โชว์ "ผลลัพธ์" ให้เห็น = proof ที่คนซื้อเชื่อ, คุมเฟรมเริ่ม-จบได้เอง |
| 4 | **Google Flow** | F4 สินค้าพูดได้ | ไวรัลง่าย ต้นทุนต่ำ แต่คอนเวอร์ชันน้อยกว่า F1 |
| 5 | **Meta AI** | M1 Animate รูปสินค้า (B-roll) | **ฟรี + เร็ว** ใช้ทำช็อตเสริม/ทดสอบไอเดียก่อนเสียเครดิต Flow |
| 6 | **Meta AI** | M2 ฉาก lifestyle สั้น | ใช้เป็นช็อตเปิด/บรรยากาศ ไม่ควรให้เป็นช็อตที่โชว์สินค้าหลัก |

**สรุปสั้น:** ใช้ **Flow เป็นตัวหลัก** (ทำคลิปที่ขาย), ใช้ **Meta AI เป็นตัวเสริม** (ช็อตประกอบฟรี) — ไม่แนะนำให้ Meta AI ทำช็อตที่โชว์สินค้าชัดๆ เพราะคุมความเหมือนของสินค้ายากกว่า และยังไม่มีข้อมูลยืนยันชัดว่าเสียงพูดไทยใช้ได้เสถียร

---

## เทียบ 2 เครื่องมือ

| | Google Flow (Veo 3.1) | Meta AI (แอป Meta AI / Vibes / FB / IG / Messenger) |
|---|---|---|
| ใส่รูปสินค้าเป็นอ้างอิง | ✅ **Ingredients to Video** (สินค้า + ตัวละคร + ฉาก) | ✅ อัปรูปแล้วพิมพ์ขึ้นต้นด้วย **"Animate ..."** |
| คุมเฟรมเริ่ม-จบ | ✅ **Frames to Video** | ❌ |
| ต่อคลิปให้ยาว | ✅ **Extend** | จำกัด |
| ความยาวต่อครั้ง | 4 / 6 / 8 วิ | animate รูป ~5 วิ (ตามบทความไทย), Vibes อ้างสูงสุด ~15 วิ (ยังไม่ยืนยัน) |
| เสียง/บทพูดไทย | ✅ ใส่บทพูดไทยในพรอมท์ได้ + SFX + เสียงบรรยากาศ | ⚠️ ข้อมูลขัดกัน: บางบทความว่าได้ บางแหล่งว่ายังไม่รองรับ → ต้องลองเอง |
| ค่าใช้จ่าย | เครดิต: Lite 10 / Fast 20 / Quality 100 ต่อครั้ง (Ultra ลดครึ่งสำหรับ Lite/Fast); ฟรี ~50 เครดิต/วัน (แหล่งข้อมูลไม่ตรงกัน) | ฟรี |
| เหมาะกับ | ช็อตขายของหลัก, ตัวละครคนเดิมข้ามคลิป | B-roll, ทดสอบไอเดีย, คลิปลง Reels/FB |

**ทริคประหยัดเครดิต Flow:** ร่างด้วย **Lite/Fast** ก่อน → อันไหนเวิร์ค ค่อยเจนใหม่ด้วย **Quality** เฉพาะช็อตที่จะใช้จริง

---

## (ก) สิ่งที่ดึงมาได้จริงจากแหล่ง

### Google Flow / Veo (ทางการ — Google Cloud)
- สูตร: **[Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]**
- บทพูด: `A woman says, "We have to leave now."`
- เสียง: `SFX: thunder cracks in the distance` / `Ambient noise: the quiet hum of a starship bridge`
- Ingredients: `Using the provided images for the detective, the woman, and the office setting, create a medium shot of the detective behind his desk. He looks up at the woman and says in a weary voice, "Of all the offices in this town, you had to walk into mine."`
- Frames to video: `The camera performs a smooth 180-degree arc shot, starting with the front-facing view of the singer and circling around her to seamlessly end on the POV shot from behind her on stage.`
- สิ่งที่ไม่อยากได้ให้เขียนเชิงบวก: "a desolate landscape with no buildings or roads" แทน "no man-made structures"

### สินค้า/สิ่งของพูดได้ (Lemon8 @nattawut.puphet, Gemini Imagen 4 + Veo 3.1)
- ขั้น 1 สร้างรูป "แก้วกาแฟการ์ตูนตาโต" ขั้น 2 อัปรูปเข้าโหมดวิดีโอแล้วสั่ง: `Make this glass move your mouth, say, 'Good morning Monday, sir.'` (+ ระบุน้ำเสียงผู้ชายอบอุ่น)

### เช็กลิสต์บทพูด (COMSIAM)
ระบุให้ครบ: **ใครพูด • พูดภาษาอะไร • พูดประโยคไหน • น้ำเสียงแบบไหน • หันไปทางไหน • พูดก่อน/หลังการกระทำ • มีดนตรีไหม • มีซับไหม**

### Flow + ChatGPT (Lemon8 @kingpirate91)
- เตรียมแค่ **ภาพตัวละคร + ภาพสินค้า + ชื่อสินค้า** → ให้ ChatGPT ประมวลผลออกมาเป็นพรอมท์ยาวสำเร็จรูป → เอาไปใช้ใน Flow (ตัวพรอมท์จริงอยู่ในคอมเมนต์ 3 อัน — เปิดดูไม่ได้)

### Meta AI (Meta Help Center + บทความไทย)
- อัปรูป → พิมพ์ขึ้นต้นด้วย **"Animate"** + อธิบายให้ละเอียด
- สร้างวิดีโอจากแชทได้ โดยบรรยาย ตัวละคร / ฉาก / การกระทำ / บทพูด / เสียง
- ตัวอย่างทางการมีแค่แบบง่าย เช่น "cat playing piano in space"

### Guardrail สำหรับ animate รูปสินค้า (หลายแหล่ง)
`Keep the bottle shape, color, label, and position unchanged.` + เลี่ยง packaging บิด, โลโก้เปลี่ยน, สินค้าเกิน, ตัวหนังสืออ่านไม่ออก

---

## (ข) พรอมท์พร้อมใช้

> วิธีใช้: แก้เฉพาะในวงเล็บ `[ ]` — พรอมท์เขียนภาษาอังกฤษ (โมเดลเข้าใจแม่นกว่า) แต่**บทพูดเป็นภาษาไทย**ในเครื่องหมายคำพูด
> ทุกพรอมท์ตั้ง **9:16** ในตัวเลือกของเครื่องมือด้วย (ไม่ใช่แค่เขียนในพรอมท์)

### 🥇 F1 — Flow: ตัวละครคนเดิมรีวิว + ถือสินค้า (Ingredients to Video)
**อัปโหลด:** ① รูปสินค้าจริง (พื้นหลังเรียบ เห็นฉลากชัด) ② รูปตัวละคร (เจนจาก Nano Banana แล้วเก็บไว้ใช้ทุกคลิป) ③ (ถ้ามี) รูปฉาก

ช็อต 1 — ฮุก (8 วิ)
```
Using the provided images of the woman, the [product name] and the bedroom setting.
Vertical smartphone UGC video, handheld medium close-up with slight natural shake, soft morning daylight from a window.
The woman picks up the [product name] and holds it close to the camera so the label is clearly readable,
then looks straight into the lens and says in Thai with an excited, friendly tone:
"[ฮุก ≤ 1 ประโยค เช่น ใครผมชี้ฟูตอนเช้า หยุดดูก่อน!]"
The product keeps exactly the same shape, color, size and label as the reference image; her hands look natural.
Ambient noise: quiet bedroom room tone. No music, no subtitles.
```

ช็อต 2 — เดโม/พิสูจน์ (8 วิ)
```
Using the same provided images of the woman and the [product name].
Close-up, handheld, same lighting and outfit as before.
She [แสดงการใช้งาน 1 อย่าง เช่น sprays it twice onto her hair and combs through once];
the result is clearly visible: [ผลที่เห็นได้ เช่น the frizz smooths down].
She says in Thai, calm and genuine: "[บทพูดสั้น เช่น หวีทีเดียว เรียบเลย]"
SFX: [เสียงการใช้งาน เช่น two soft spray sounds]. Ambient noise: quiet room tone. No music.
The product stays fully visible and identical to the reference image.
```

ช็อต 3 — CTA (6–8 วิ)
```
Using the same provided images of the woman and the [product name].
Medium shot, handheld. She holds the [product name] beside her face, smiles, points down toward the bottom of the screen and says in Thai:
"[CTA เช่น ราคาไม่ถึงสองร้อย กดตะกร้าด้านล่างได้เลย]"
Clean, uncluttered background with only her and the product. No music, no subtitles.
```

**ดียังไง:** ตรงสูตร UGC ที่ขายได้ (ฮุก 2 วิแรก → เดโมให้เห็นผล → CTA เดียว), ใช้รูปสินค้าจริงเป็น ingredient = สินค้าไม่เพี้ยน (ผ่านกฎ Shopee), ตัวละครคนเดิมทุกคลิป = ช่องมีภาพจำ
**ระวัง:** อย่าให้พูดว่า "ใช้มา 3 เดือน" ถ้าไม่จริง, ห้ามอ้างสรรพคุณทางการแพทย์, ห้ามใช้หน้าคนจริง/เด็ก

---

### 🥈 F2 — Flow: หมี Bear Friends ขายของ (Ingredients to Video)
**อัปโหลด:** ① รูปหมีของช่อง ② รูปสินค้าจริง
```
Using the provided images of the bear character and the [product name].
Vertical 3D animated video in a soft, cute Pixar-like style, cozy pastel living room, warm light.
Medium shot: the bear notices the [product name] on the table, gasps happily, picks it up with both paws
and turns it toward the camera so the front label faces the viewer.
The bear says in Thai with a cheerful, childlike voice: "[บทพูด เช่น อันนี้แหละ ที่ทำให้ห้องหมีหอมทั้งวัน!]"
Then the camera slowly pushes in on the product.
SFX: a soft sparkle when the bear lifts the product. Ambient noise: gentle, playful room tone.
The [product name] is rendered realistically and keeps exactly the colors, shape and label of the reference image.
```
**ดียังไง:** ใช้ตัวละครที่ช่องมีอยู่แล้ว (ต่อยอดซีรีส์ได้), การ์ตูนเลี่ยงประเด็นปลอมหน้าคนจริง, แยกตัวจากคลิป UGC AI ที่ล้นตลาด
**ทริค:** สั่งให้ "สินค้า render แบบเหมือนจริง" แม้ฉากเป็นการ์ตูน → ลูกค้าเห็นของจริงชัด

---

### 🥉 F3 — Flow: ก่อน/หลัง (Frames to Video)
**เตรียม:** เฟรมแรก = สภาพ "ก่อน" (เช่น โต๊ะรก), เฟรมสุดท้าย = สภาพ "หลัง" ที่มีสินค้า (ทำทั้งสองรูปใน Nano Banana จากรูปสินค้าจริง)
```
Vertical video. Top-down handheld shot of a home-office desk.
Starting from the messy desk in the first frame, a pair of hands slides the [product name] into the frame
and quickly places the items into it one by one, ending exactly on the tidy desk shown in the last frame.
Smooth, satisfying motion, natural daylight.
SFX: soft clicks and taps as each item is placed. Ambient noise: quiet room. Light upbeat music.
```
**ดียังไง:** ภาพ "ผลลัพธ์" พูดแทนสรรพคุณ = น่าเชื่อกว่าพูดอวด, คุมฉากจบได้แน่นอน (ไม่ลุ้น)
**ระวัง:** ผลลัพธ์ต้องสมจริง ห้ามทำให้ดีเกินกว่าที่สินค้าทำได้จริง

---

### F4 — Flow: สินค้าพูดได้ (Frames/Ingredients)
**เตรียม:** เจนรูปสินค้าแบบมีตาการ์ตูนบนพื้นผิวเดิม (ใน Nano Banana) โดยยังเห็นฉากลากชัด
```
Using the provided image of the [product name] with cartoon eyes and mouth.
Vertical video, static eye-level shot on a wooden table, soft daylight.
The [product name] blinks, its mouth moves in sync with the speech, and it says in Thai with a [น้ำเสียง เช่น warm, playful male voice]:
"[บทพูด ≤ 1 ประโยค เช่น ร้อนแบบนี้ เอาหนูไปด้วยสิ!]"
The product's real shape, color and label stay unchanged; only the eyes and mouth move.
No music, no subtitles.
```
**ดียังไง:** หยุดนิ้วคนเลื่อนฟีดได้ดี ทำเร็ว ใช้เครดิตน้อย (ช็อตเดียว)
**ข้อด้อย:** ตลก/ไวรัลมากกว่าขาย — ใช้คู่กับช็อตเดโม F1/F3 จะดีกว่า

---

### M1 — Meta AI: Animate รูปสินค้า (B-roll ฟรี)
อัปรูปสินค้าจริงในแอป Meta AI แล้วพิมพ์:
```
Animate this product photo: slow, smooth camera push-in with a gentle rotation,
soft light sweeping across the surface, a few light dust particles in the air.
Keep the product's shape, color, label, logo and position exactly unchanged.
Plain clean background, no extra objects, no added text.
```
**ดียังไง:** ฟรี ได้ช็อตเปิด/ปิดสวยๆ ไว้แทรกระหว่างช็อต Flow ลดเครดิต
**ระวัง:** ตรวจฉลาก/โลโก้ทุกครั้ง ถ้าเพี้ยนให้ทิ้ง (Shopee ห้ามสินค้าต่างจากของจริง)

### M2 — Meta AI: ฉาก lifestyle เปิดเรื่อง (ไม่โชว์สินค้า)
```
Imagine a short vertical video: a hot, sunny Bangkok afternoon, a young person in a small apartment
fanning themselves and sighing, sweat on their forehead, warm golden light, handheld phone-camera feel.
```
**ดียังไง:** ใช้เป็นช็อต "ปัญหา" ก่อนตัดเข้าช็อตสินค้าจาก Flow (เช่น พัดลมพกพา) — ไม่มีสินค้าในช็อตนี้เลยไม่เสี่ยงสินค้าเพี้ยน
**หมายเหตุ:** Meta AI รับพรอมท์ภาษาไทยได้ แต่ภาษาอังกฤษมักได้ผลแม่นกว่า; เสียงพูดไทยให้ลองเทสต์ก่อน ถ้าไม่ได้ให้พากย์เอง/ใส่ใน CapCut

---

### Meta-prompt: ให้ ChatGPT/Gemini เขียนพรอมท์ Flow ให้ (แบบที่ @kingpirate91 ใช้)
```
คุณคือผู้เชี่ยวชาญเขียนพรอมท์ Google Flow (Veo 3.1) สำหรับคลิปขายของ Shopee Affiliate
ฉันจะแนบ: รูปตัวละคร, รูปสินค้า และชื่อสินค้า "[ชื่อสินค้า]" ราคา [ราคา] จุดเด่น [1-3 ข้อ] ปัญหาที่แก้ [ปัญหา]

ให้เขียนพรอมท์ภาษาอังกฤษ 3 ช็อต (ฮุก / เดโม / CTA) ช็อตละไม่เกิน 8 วินาที สำหรับโหมด Ingredients to Video:
- ขึ้นต้นทุกช็อตด้วย "Using the provided images of ..."
- ใช้สูตร Cinematography + Subject + Action + Context + Style
- บทพูดเป็นภาษาไทยในเครื่องหมายคำพูด ช็อตละไม่เกิน 1 ประโยค พร้อมระบุน้ำเสียง
- ระบุ SFX และ Ambient noise แยกบรรทัด ไม่มีซับในวิดีโอ
- สินค้าต้องเหมือนรูปอ้างอิงทุกอย่าง (รูปทรง สี ขนาด ฉลาก)
- ห้ามอ้างสรรพคุณเกินจริง/ทางการแพทย์ ห้ามทำเป็นรีวิวว่าใช้จริงมานาน
แล้วเขียนแคปชันไทย 2 บรรทัด + แฮชแท็ก 5 อัน (มี #AIgenerated) ให้ด้วย
```

---

## ก่อนโพสต์ Shopee Video
- [ ] เปิดปุ่ม **AI-generated** (Shopee SG: ไม่เปิด = หัก 3 คะแนน + ลบคลิป; ไทยยังไม่เจอประกาศทางการ ควรเปิดไว้ก่อน)
- [ ] สินค้าในคลิปตรงกับของจริงทุกช็อต
- [ ] ปักตะกร้าให้ไอคอนโผล่ช่วงที่เห็นสินค้า

## แหล่งอ้างอิง
- Google Cloud — [Ultimate prompting guide for Veo 3.1](https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-veo-3-1)
- Google — [Veo 3.1 ใน Gemini API](https://ai.google.dev/gemini-api/docs/veo)
- Lemon8 @nattawut.puphet — [สิ่งของพูดได้ด้วย Gemini](https://www.lemon8-app.com/@nattawut.puphet/7604010460316303890?region=us), [แจกฟรี 20 Prompt](https://www.lemon8-app.com/@nattawut.puphet/7608824453878809095?region=th)
- Lemon8 @kingpirate91 — [แจก PROMPT รีวิวสินค้า ChatGPT + FLOW](https://www.lemon8-app.com/@kingpirate91/7609042926928183815?region=th)
- COMSIAM — [วิธีสร้างวิดีโอพร้อมเสียงด้วย Gemini](https://comsiam.com/gemini-video-with-audio/)
- Meta — [Edit/animate images with Meta AI and Vibes](https://www.meta.com/help/artificial-intelligence/517678174532704/)
- [วิธีสร้างวิดีโอ AI ฟรีด้วย Meta AI พร้อมเสียงภาษาไทย](https://www.metaverseresolution.com/post/create-ai-video-meta-ai-thai), [Marketing Oops: Meta AI รองรับภาษาไทย](https://www.marketingoops.com/tech-2/meta-ai-thai-language-how-to/)
- Meta Vibes — [ScreenApp review](https://screenapp.io/blog/meta-vibes-app-ai-video-generation-review), [Android Central](https://www.androidcentral.com/apps-software/meta/meta-ai-app-new-vibes-feed-full-ai-generated-videos-you-can-remix)
- Flow pricing — [Magic Hour](https://magichour.ai/blog/google-flow), [DIYAI](https://diyai.io/ai-tools/video-generation/google-veo-pricing/)
- Shopee SG — [AIGC on Shopee Video](https://help.shopee.sg/portal/10/article/201777)
