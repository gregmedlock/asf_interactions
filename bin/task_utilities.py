# Task utilities: functions used across multiple tasks
import cobra
import pandas as pd

def create_media_dict(media_filename, universal_model, estimated_uptake=False):
    '''
    Read a media file and create a media dictionary. Use a universal model so
    all objects are created before calling the function.

    in:
    media_filename - string specifying media file. file must have metabolite ids
                     as index when read as a dataframe.
    universal_model - cobra.core.Model object. Any metabolites specified in the
                      media file that are missing from this model will not be
                      included in the media dictionary

    out:
    media_dict - dictionary of {cpd_id:lower_bound}.

    '''

    media = pd.DataFrame.from_csv(media_filename,sep=',')
    media_dict = {}
    met_ids = list(media.index)
    met_ids = [x + '_c' for x in met_ids] # universal model will have _c suffix
    universal_met_ids = [met.id for met in universal_model.metabolites]
    for met in met_ids:
        if met in universal_met_ids:
            # find met in universal model
            met_obj = universal_model.metabolites.get_by_id(met).copy()
            met_obj.id = met_obj.id[:-1] + 'e'# switch c to e
            if estimated_uptake:
                met_index = met.split('_c')[0] # get cpd ID without compartment
                media_dict[met_obj] = -1*media.loc[met_index,'estimated_uptake']
            else:
                media_dict[met_obj] = -1000.0 # For now, assume -1000 instead of any values in the media file
        else:
            print('WARNING: metabolite ' + met + ' is not in universal model. Excluded from media.')
    return media_dict

def open_exchanges(model):
    '''
    Open all exchange reactions in a model.

    in:
    model - cobra.core.Model object

    out:
    None

    '''
    for reaction in [reaction.id for reaction in model.reactions]:
        if reaction.startswith('EX_'):
            ex_rxn = model.reactions.get_by_id(reaction)
            ex_rxn.lower_bound = -1000
            ex_rxn.upper_bound = 1000

def close_exchanges(model):
    '''
    Close all exchange reactions in a model.

    in:
    model - cobra.core.Model object

    out:
    None
    '''
    for reaction in [reaction.id for reaction in model.reactions]:
        if reaction.startswith('EX_'):
            ex_rxn = model.reactions.get_by_id(reaction)
            ex_rxn.lower_bound = 0.0
            ex_rxn.upper_bound = 0.0


def set_media(model, media, verbose=False):
    '''
    Set exchange bounds for model according to metabolite and bounds in media. Model is changed in place
    (e.g. the original object is modified; None is returned). Metabolite
    ids in the dictionary should be cpd#####_e for consistency with modelSEED ids.

    in:
    model - cobra.core.Model object
    media - dictionary of {cobra.core.Metabolite:lower_bound}, where lower bound is a float

    out:
    None
    '''

    # Find and close all exchange reactions in the model
    model_rxns = [rxn.id for rxn in model.reactions]
    for rxn in model_rxns:
        if rxn.startswith('EX_') and rxn.endswith('_e'):
            model.reactions.get_by_id(rxn).lower_bound = 0.0

    # Check for existence of exchange reactions for the media metabolites in the model
    for met in media.keys():
        if 'EX_'+met.id in model_rxns:
            model.reactions.get_by_id('EX_'+met.id).lower_bound = media[met]
        else:
            # Create exchange reaction and add to model
            if verbose:
                print("added exchange rxn for " + met.name)
            new_exchange = cobra.Reaction('EX_'+met.id)
            new_exchange.name = met.name + ' exchange'
            new_exchange.add_metabolites({met:-1})
            new_exchange.lower_bound = media[met]
            new_exchange.upper_bound = 1000
            model.add_reaction(new_exchange)
            model.repair()
