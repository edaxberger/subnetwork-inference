import copy

import numpy as np
import torch
from torchvision import datasets, transforms
from sklearn.metrics import roc_curve, auc

from utils import DatafeedImage


def load_corrupted_dataset(dname, severity, data_dir='../../data', batch_size=256, cuda=True, workers=4, n_data=None, subset_idx=-1):
    assert dname in ['CIFAR10', 'CIFAR100', 'Imagenet']

    transform_dict = {
        'CIFAR10': transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616)),
        ]),
        'CIFAR100': transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.5071, 0.4866, 0.4409), (0.2673, 0.2564, 0.2762)),
        ]),
        'Imagenet': transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ]),
    }

    if dname == 'CIFAR10':
        x_file = data_dir + '/CIFAR-10-C/CIFAR10_c%d.npy' % severity
        np_x = np.load(x_file)
        y_file = data_dir + '/CIFAR-10-C/CIFAR10_c_labels.npy'
        np_y = np.load(y_file).astype(np.int64)

        # subsample dataset if desired (either randomly or by subset index)
        if n_data is not None:
            if subset_idx == -1:
                np.random.seed(0)
                perm = np.random.permutation(np_x.shape[0])
                subset = perm[:n_data]
            else:
                subset = list(range(subset_idx * n_data, (subset_idx+1) * n_data))
            np_x = np_x[subset]
            np_y = np_y[subset]

        dataset = DatafeedImage(np_x, np_y, transform_dict[dname])

    elif dname == 'CIFAR100':
        x_file = data_dir + '/CIFAR-100-C/CIFAR100_c%d.npy' % severity
        np_x = np.load(x_file)
        y_file = data_dir + '/CIFAR-100-C/CIFAR100_c_labels.npy'
        np_y = np.load(y_file).astype(np.int64)
        dataset = DatafeedImage(np_x, np_y, transform_dict[dname])

    elif dname == 'Imagenet':
        dataset = datasets.ImageFolder(
            data_dir + '/imagenet-c/%d' % severity,
            transform_dict[dname])

        # subsample dataset if desired (either randomly or by subset index)
        if n_data is not None:
            if subset_idx == -1:
                np.random.seed(0)
                perm = np.random.permutation(len(dataset.samples))
                subset = perm[:n_data]
            else:
                subset = list(range(subset_idx * n_data, (subset_idx+1) * n_data))

            dataset.samples = [dataset.samples[i] for i in subset]
            dataset.targets = [dataset.targets[i] for i in subset]

    loader = torch.utils.data.DataLoader(
        dataset,
        batch_size=batch_size, shuffle=False,
        num_workers=workers, pin_memory=cuda)

    return loader


def rotate_load_dataset(dname, angle, data_dir='../../data', batch_size=256, cuda=True, workers=4, n_data=None, subset_idx=-1):
    assert dname in ['MNIST', 'Fashion', 'SVHN', 'CIFAR10', 'CIFAR100']

    transform_dict = {
        'MNIST': transforms.Compose([
            transforms.RandomRotation([angle, angle], resample=2, expand=False, center=None),
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.1307,), std=(0.3081,))
        ]),
        'Fashion': transforms.Compose([
            transforms.RandomRotation([angle, angle], resample=2, expand=False, center=None),
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.2860,), std=(0.3530,))
        ]),
        'SVHN': transforms.Compose([
            transforms.RandomRotation([angle, angle], resample=2, expand=False, center=None),
            transforms.ToTensor(),
            transforms.Normalize((0.4377, 0.4438, 0.4728), (0.1980, 0.2010, 0.1970)),
        ]),
        'CIFAR10': transforms.Compose([
            transforms.RandomRotation([angle, angle], resample=2, expand=False, center=None),
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616)),
        ]),
        'CIFAR100': transforms.Compose([
            transforms.RandomRotation([angle, angle], resample=2, expand=False, center=None),
            transforms.ToTensor(),
            transforms.Normalize((0.5071, 0.4866, 0.4409), (0.2673, 0.2564, 0.2762)),
        ]),
        'SmallImagenet': None,
        'Imagenet': None,
    }

    dataset_dict = {
        'MNIST': datasets.MNIST,
        'Fashion': datasets.FashionMNIST,
        'SVHN': datasets.SVHN,
        'CIFAR10': datasets.CIFAR10,
        'CIFAR100': datasets.CIFAR100,
        'SmallImagenet': None,
        'Imagenet': None,
    }

    dset_kwargs = {
        'root': data_dir,
        'train': False,
        'download': True,
        'transform': transform_dict[dname]
    }

    if dname == 'SVHN':
        del dset_kwargs['train']
        dset_kwargs['split'] = 'test'

    source_dset = dataset_dict[dname](**dset_kwargs)

    # subsample source dataset if desired (either randomly or by subset index)
    if n_data is not None:
        if subset_idx == -1:
            np.random.seed(0)
            perm = np.random.permutation(source_dset.data.shape[0])
            subset = perm[:n_data]
        else:
            subset = list(range(subset_idx * n_data, (subset_idx+1) * n_data))
        source_dset.data = source_dset.data[subset]
        source_dset.targets = source_dset.targets[subset]

    source_loader = torch.utils.data.DataLoader(
        source_dset,
        batch_size=batch_size, shuffle=False,
        num_workers=workers, pin_memory=cuda)

    return source_loader


def cross_load_dataset(dname_source, dname_target, data_dir='../../data', batch_size=256,
                       cuda=True, workers=4, n_data=None, subset_idx=-1):
    assert dname_source in ['MNIST', 'Fashion', 'KMNIST', 'SVHN', 'CIFAR10', 'CIFAR100']
    assert dname_target in ['MNIST', 'Fashion', 'KMNIST', 'SVHN', 'CIFAR10', 'CIFAR100']

    transform_dict = {
        'MNIST': transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.1307,), std=(0.3081,))
        ]),
        'Fashion': transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.2860,), std=(0.3530,))
        ]),
        'KMNIST': transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.1918,), std=(0.3483,))
        ]),
        'SVHN': transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.4377, 0.4438, 0.4728), (0.1980, 0.2010, 0.1970)),
        ]),
        'CIFAR10': transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616)),
        ]),
        'CIFAR100': transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.5071, 0.4866, 0.4409), (0.2673, 0.2564, 0.2762)),
        ]),
        'SmallImagenet': None,
        'Imagenet': None,
    }

    dataset_dict = {'MNIST': datasets.MNIST,
                    'Fashion': datasets.FashionMNIST,
                    'KMNIST': datasets.KMNIST,
                    'SVHN': datasets.SVHN,
                    'CIFAR10': datasets.CIFAR10,
                    'CIFAR100': datasets.CIFAR100,
                    'SmallImagenet': None,
                    'Imagenet': None,
                    }

    dset_kwargs = {'root': data_dir,
                   'train': False,
                   'download': True,
                   'transform': transform_dict[dname_source]}

    source_dset_kwargs = dset_kwargs
    target_dset_kwargs = copy.copy(dset_kwargs)
    if dname_source == 'SVHN':
        del source_dset_kwargs['train']
        source_dset_kwargs['split'] = 'test'
    if dname_target == 'SVHN':
        del target_dset_kwargs['train']
        target_dset_kwargs['split'] = 'test'

    source_dset = dataset_dict[dname_source](**source_dset_kwargs)
    target_dset = dataset_dict[dname_target](**target_dset_kwargs)

    # subsample target dataset if desired (either randomly or by subset index)
    if n_data is not None:
        if subset_idx == -1:
            np.random.seed(0)
            perm = np.random.permutation(target_dset.data.shape[0])
            subset = perm[:n_data]
        else:
            subset = list(range(subset_idx * n_data, (subset_idx+1) * n_data))
        target_dset.data = target_dset.data[subset]
        if dname_target == "SVHN":
            target_dset.labels = target_dset.labels[subset]
        else:
            target_dset.targets = target_dset.targets[subset]

    source_loader = torch.utils.data.DataLoader(
        source_dset,
        batch_size=batch_size, shuffle=False,
        num_workers=workers, pin_memory=cuda)

    target_loader = torch.utils.data.DataLoader(
        target_dset,
        batch_size=batch_size, shuffle=False,
        num_workers=workers, pin_memory=cuda)

    return source_loader, target_loader


def get_roc_params(ID_entropy, OOD_entropy):
    if torch.is_tensor(ID_entropy):
        ID_entropy = ID_entropy.data.cpu().numpy()
    if torch.is_tensor(OOD_entropy):
        OOD_entropy = OOD_entropy.data.cpu().numpy()

    targets = np.concatenate([np.ones(OOD_entropy.shape[0]), np.zeros(ID_entropy.shape[0])], axis=0)
    entropy_vals = np.concatenate([OOD_entropy, ID_entropy], axis=0)
    fpr, tpr, _ = roc_curve(targets, entropy_vals)
    roc_auc = auc(fpr, tpr)
    return fpr, tpr, roc_auc


# def evaluate_predictive_entropy_DUN(net, loader, eps=1e-35):
#     entropy_vec = []
#     for images, _ in loader:
#         probs = net.predict(images).data
#         entropy = -(probs * probs.clamp(min=eps).log()).sum(dim=1).cpu().numpy()
#         entropy_vec.append(entropy)
#     entropy_vec = np.concatenate(entropy_vec, axis=0)
#     return entropy_vec


# def get_angle_entropy_DUN(net, dname, data_dir='../../data', stop_angle=180, step=10,
#                           batch_size=256, cuda=True, workers=4):
#     angles = np.arange(0, stop_angle + 5, step)

#     angle_entropy_vec = []
#     for angle in angles:
#         print(angle)
#         loader = rotate_load_dataset(dname, angle, data_dir=data_dir,
#                                      batch_size=batch_size, cuda=cuda, workers=workers)

#         entropy = evaluate_predictive_entropy_DUN(net, loader, eps=1e-35)
#         angle_entropy_vec.append(entropy)
#     angle_entropy_vec = np.stack(angle_entropy_vec, axis=0)
#     return angles, angle_entropy_vec


# def get_preds_targets_DUN(net, loader):
#     prob_vec = []
#     target_vec = []
#     for images, target in loader:
#         probs = net.predict(images).data
#         prob_vec.append(probs)
#         target_vec.append(target)

#     prob_vec = torch.cat(prob_vec, dim=0)
#     target_vec = torch.cat(target_vec, dim=0)
#     return prob_vec.data.cpu(), target_vec.data.cpu()
